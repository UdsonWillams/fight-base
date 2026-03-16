#!/usr/bin/env python3
"""
🤖 Treinamento Local do Modelo de Predição MMA (Otimizado & Async)

Este script treina um modelo de ML para prever o vencedor de lutas de MMA.
Utiliza uma abordagem de "Janela Expansiva" (Time-Series) para calcular
estatísticas acumuladas até o dia da luta, eliminando Data Leakage.

Uso:
    python scripts/train_model_local.py

Saída:
    models/mma_model_v1.joblib
"""
import re
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATASET_PATH = PROJECT_ROOT / "datasets" / "UFC.csv"
FIGHTER_DETAILS_PATH = PROJECT_ROOT / "datasets" / "fighter_details.csv"
OUTPUT_DIR = PROJECT_ROOT / "models"
OUTPUT_MODEL_PATH = OUTPUT_DIR / "mma_model_v1.joblib"

# 🎯 Features atualizadas: Adicionamos Idade e Base
TARGET_FEATURES = [
    "height_diff", "weight_diff", "reach_diff", "splm_diff",
    "sapm_diff", "td_def_diff", "td_avg_diff", "sub_avg_diff",
    "str_acc_diff", "wins_diff", "losses_diff", 
    "age_diff", "is_opposite_stance" # <-- Novas Super Features
]

# ============================================================================
# FUNÇÕES DE PROCESSAMENTO (CPU-BOUND)
# ============================================================================

def safe_val(val, default=0.0):
    """Garante que valores nulos do pandas se tornem um valor numérico seguro."""
    return float(val) if pd.notna(val) else default

def build_time_series_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constrói features dinamicamente simulando o tempo.
    Calcula o histórico do lutador *antes* da luta acontecer.
    """
    print("⏳ Construindo features cronológicas (Zero Data Leakage)...")
    
    # 1. Ordenação Cronológica Estrita
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values(by="date", ascending=True).reset_index(drop=True)
    
    fighter_state = {}
    
    def get_initial_state():
        return {
            "fights": 0, "wins": 0, "losses": 0,
            "total_time_min": 0.0,
            "sig_str_landed": 0.0, "sig_str_atmpted": 0.0, "sig_str_absorbed": 0.0,
            "td_landed": 0.0, "sub_att": 0.0,
            "opp_td_landed": 0.0, "opp_td_atmpted": 0.0 
        }

    rows = []

    # 2. Iterar no tempo
    for row in df.itertuples(index=False):
        r_id = getattr(row, "r_id", np.nan)
        b_id = getattr(row, "b_id", np.nan)
        winner_id = getattr(row, "winner_id", np.nan)
        fight_date = getattr(row, "date", None)
        
        if pd.isna(winner_id) or pd.isna(r_id) or pd.isna(b_id):
            continue

        target = 1 if winner_id == r_id else 0

        # Inicializa lutadores estreantes
        if r_id not in fighter_state: fighter_state[r_id] = get_initial_state()
        if b_id not in fighter_state: fighter_state[b_id] = get_initial_state()

        r = fighter_state[r_id]
        b = fighter_state[b_id]

        # --- A. CALCULAR FEATURES (Baseado apenas no passado) ---
        def calc_stats(st):
            mins = max(st["total_time_min"], 1.0)
            fights = max(st["fights"], 1.0)
            str_att = max(st["sig_str_atmpted"], 1.0)
            opp_td_att = max(st["opp_td_atmpted"], 1.0)

            return {
                "splm": st["sig_str_landed"] / mins,
                "sapm": st["sig_str_absorbed"] / mins,
                "str_acc": (st["sig_str_landed"] / str_att) * 100,
                "td_avg": st["td_landed"] / fights,
                "sub_avg": st["sub_att"] / fights,
                "td_def": (1.0 - (st["opp_td_landed"] / opp_td_att)) * 100 if st["opp_td_atmpted"] > 0 else 50.0
            }

        r_stats = calc_stats(r)
        b_stats = calc_stats(b)

        # Salva a linha da luta. As features estáticas (físicas, base, idade) entram depois.
        rows.append({
            "r_id": r_id, "b_id": b_id, "fight_date": fight_date, 
            "height_diff": 0.0, "weight_diff": 0.0, "reach_diff": 0.0,
            "age_diff": 0.0, "is_opposite_stance": 0, 
            "splm_diff": r_stats["splm"] - b_stats["splm"],
            "sapm_diff": r_stats["sapm"] - b_stats["sapm"],
            "td_def_diff": r_stats["td_def"] - b_stats["td_def"],
            "td_avg_diff": r_stats["td_avg"] - b_stats["td_avg"],
            "sub_avg_diff": r_stats["sub_avg"] - b_stats["sub_avg"],
            "str_acc_diff": r_stats["str_acc"] - b_stats["str_acc"],
            "wins_diff": float(r["wins"]) - float(b["wins"]),
            "losses_diff": float(r["losses"]) - float(b["losses"]),
            "target": target
        })

        # --- B. ATUALIZAR ESTADO (Após a luta) ---
        match_time_sec = safe_val(getattr(row, "match_time_sec", 0))
        if match_time_sec == 0:
            match_time_sec = safe_val(getattr(row, "finish_round", 1)) * 300
        match_time_min = match_time_sec / 60.0

        r_str_landed = safe_val(getattr(row, "r_sig_str_landed"))
        b_str_landed = safe_val(getattr(row, "b_sig_str_landed"))
        r_td_landed = safe_val(getattr(row, "r_td_landed"))
        b_td_landed = safe_val(getattr(row, "b_td_landed"))
        r_td_att = safe_val(getattr(row, "r_td_atmpted"))
        b_td_att = safe_val(getattr(row, "b_td_atmpted"))

        # Red Stats
        r["fights"] += 1
        r["total_time_min"] += match_time_min
        r["sig_str_landed"] += r_str_landed
        r["sig_str_atmpted"] += safe_val(getattr(row, "r_sig_str_atmpted"))
        r["sig_str_absorbed"] += b_str_landed 
        r["td_landed"] += r_td_landed
        r["sub_att"] += safe_val(getattr(row, "r_sub_att"))
        r["opp_td_landed"] += b_td_landed
        r["opp_td_atmpted"] += b_td_att
        if target == 1: r["wins"] += 1 
        else: r["losses"] += 1

        # Blue Stats
        b["fights"] += 1
        b["total_time_min"] += match_time_min
        b["sig_str_landed"] += b_str_landed
        b["sig_str_atmpted"] += safe_val(getattr(row, "b_sig_str_atmpted"))
        b["sig_str_absorbed"] += r_str_landed 
        b["td_landed"] += b_td_landed
        b["sub_att"] += safe_val(getattr(row, "b_sub_att"))
        b["opp_td_landed"] += r_td_landed
        b["opp_td_atmpted"] += r_td_att
        if target == 0: b["wins"] += 1 
        else: b["losses"] += 1

    print(f"   ✅ {len(rows)} lutas processadas com histórico impecável")
    return pd.DataFrame(rows)

def parse_ufc_measurement(val):
    if pd.isna(val): 
        return 0.0
    val_str = str(val).lower().strip()
    if not val_str or val_str in ['--', 'na', 'nan']: 
        return 0.0
    
    nums = re.findall(r'\d+', val_str)
    if not nums: 
        return 0.0
        
    if "'" in val_str or '"' in val_str:
        feet = int(nums[0])
        inches = int(nums[1]) if len(nums) > 1 else 0
        return float((feet * 12) + inches)
        
    return float(nums[0])

def calc_age(dob_str, fight_date):
    """Calcula a idade no dia da luta em anos."""
    if pd.isna(dob_str) or pd.isna(fight_date) or dob_str in ['--', '']:
        return np.nan
    try:
        # Tenta formatar a data do UFC (ex: Oct 17, 1989)
        dob = pd.to_datetime(dob_str, format="%b %d, %Y")
        age_days = (fight_date - dob).days
        return age_days / 365.25
    except:
        return np.nan

def enrich_with_physical_and_static_data(training_df: pd.DataFrame, fighter_details_path: Path) -> pd.DataFrame:
    if not fighter_details_path.exists():
        print("   ⚠️  fighter_details.csv não encontrado. Features estáticas ficarão zeradas.")
        return training_df

    try:
        details = pd.read_csv(fighter_details_path)
        print("   📏 Enriquecendo com Dados Físicos, Base e Idade...")
        
        id_col = "fighter_id" if "fighter_id" in details.columns else "id"
        
        if id_col not in details.columns:
            return training_df
            
        static_data = {}
        for row in details.itertuples(index=False):
            fid = getattr(row, id_col, np.nan)
            if pd.notna(fid):
                static_data[fid] = {
                    "height": parse_ufc_measurement(getattr(row, "height", 0)),
                    "weight": parse_ufc_measurement(getattr(row, "weight", 0)),
                    "reach": parse_ufc_measurement(getattr(row, "reach", 0)),
                    "stance": str(getattr(row, "stance", "")).lower().strip(),
                    "dob": getattr(row, "dob", np.nan)
                }

        h_diffs, w_diffs, r_diffs, age_diffs, stance_matchups = [], [], [], [], []
        
        for row in training_df.itertuples(index=False):
            r_id = getattr(row, "r_id")
            b_id = getattr(row, "b_id")
            fight_date = getattr(row, "fight_date")

            r_data = static_data.get(r_id, {})
            b_data = static_data.get(b_id, {})

            # Diferenças Físicas
            h_diffs.append(r_data.get("height", 0) - b_data.get("height", 0))
            w_diffs.append(r_data.get("weight", 0) - b_data.get("weight", 0))
            r_diffs.append(r_data.get("reach", 0) - b_data.get("reach", 0))

            # Diferença de Idade no dia da Luta
            r_age = calc_age(r_data.get("dob"), fight_date)
            b_age = calc_age(b_data.get("dob"), fight_date)
            
            if pd.notna(r_age) and pd.notna(b_age):
                age_diffs.append(r_age - b_age)
            else:
                age_diffs.append(0.0) # Fallback

            # Confronto de Bases (0 = Iguais, 1 = Opostas)
            r_stance = r_data.get("stance", "")
            b_stance = b_data.get("stance", "")
            
            if r_stance and b_stance and r_stance != "--" and b_stance != "--":
                is_opp = 1 if r_stance != b_stance else 0
            else:
                is_opp = 0 # Fallback
                
            stance_matchups.append(is_opp)

        training_df["height_diff"] = h_diffs
        training_df["weight_diff"] = w_diffs
        training_df["reach_diff"] = r_diffs
        training_df["age_diff"] = age_diffs
        training_df["is_opposite_stance"] = stance_matchups
        
        print(f"   ✅ Features Estáticas anexadas com sucesso para {len(training_df)} lutas")
    except Exception as e:
        print(f"   ⚠️  Erro crítico ao ler fighter_details: {e}")

    return training_df

def train_and_evaluate_models(X_train, y_train, X_test, y_test):
    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=200, 
            max_depth=10, 
            min_samples_leaf=5, 
            class_weight="balanced",
            random_state=42, 
            n_jobs=-1
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=150, 
            max_depth=5, 
            learning_rate=0.05, 
            class_weight="balanced", 
            random_state=42
        ),
    }

    best_model, best_accuracy, best_name = None, 0, ""

    for name, model in models.items():
        print(f"\n   🔄 Treinando {name}...")
        
        n_jobs_cv = -1 if name == "RandomForest" else None 
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy", n_jobs=n_jobs_cv)
        print(f"      CV Accuracy: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        print(f"      Test Accuracy: {accuracy:.4f}")

        if accuracy > best_accuracy:
            best_accuracy, best_model, best_name = accuracy, model, name

    print(f"\n📋 Relatório do melhor modelo ({best_name}):")
    print(classification_report(y_test, best_model.predict(X_test), target_names=["Blue Vence", "Red Vence"]))

    return best_name, best_model, best_accuracy

# ============================================================================
# ORQUESTRADOR ASSÍNCRONO
# ============================================================================

async def main_async():
    print("\n" + "=" * 80)
    print("🤖 TREINAMENTO LOCAL DO MODELO MMA (ASYNC & TIME-SERIES V2)")
    print("=" * 80 + "\n")

    if not DATASET_PATH.exists():
        print(f"❌ Dataset não encontrado: {DATASET_PATH}")
        sys.exit(1)

    print("\n📥 Passo 1: Carregando dados...")
    df = await asyncio.to_thread(pd.read_csv, DATASET_PATH)
    print(f"   ✅ {len(df)} lutas carregadas")

    print("\n🔧 Passo 2: Construindo features de treinamento...")
    training_data = await asyncio.to_thread(build_time_series_features, df)

    # Nova função de enriquecimento
    training_data = await asyncio.to_thread(enrich_with_physical_and_static_data, training_data, FIGHTER_DETAILS_PATH)

    print("\n📊 Passo 3: Preparando matrizes...")
    X = training_data[TARGET_FEATURES].fillna(0)
    y = training_data["target"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print(f"   Amostras: Treino={len(X_train)} | Teste={len(X_test)}")

    print("\n🏋️ Passo 4: Treinando modelos...")
    best_name, best_model, best_accuracy = await asyncio.to_thread(
        train_and_evaluate_models, X_train, y_train, X_test, y_test
    )

    print(f"\n   🏆 Campeão: {best_name} (Acurácia: {best_accuracy:.4f})")
    
    if hasattr(best_model, "feature_importances_"):
        print("\n📊 Importância das Features:")
        importances = best_model.feature_importances_
        for i in np.argsort(importances)[::-1]:
            bar = "█" * int(importances[i] * 50)
            print(f"   {TARGET_FEATURES[i]:20s} {importances[i]:.4f} {bar}")

    print("\n💾 Passo 5: Salvando modelo...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(joblib.dump, best_model, OUTPUT_MODEL_PATH)
    print(f"   ✅ Modelo salvo em: {OUTPUT_MODEL_PATH}")
    
    print("\n🎉 PIPELINE CONCLUÍDO COM SUCESSO!\n")

if __name__ == "__main__":
    asyncio.run(main_async())