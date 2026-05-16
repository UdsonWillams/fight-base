#!/usr/bin/env python3
"""
🤖 Treinamento do Modelo de Predição MMA V2 — Stacking Ensemble (23 features)

Diferenças vs V1:
    - 21 features (18 V1 + ctrl_time_diff + reach_td_def + age_experience)
    - Stacking ensemble: RF + HGB → LogisticRegression
    - Lê do UFC.csv (mesmo dataset do V1)
    - Salva como mma_model_v2.joblib

Uso:
    python scripts/train_model_v2_db.py
    python scripts/train_model_v2_db.py --quick

Saída:
    models/mma_model_v2.joblib          # Stacking ensemble
    models/mma_model_v2_metadata.json   # Model Card
"""

from __future__ import annotations

import argparse
import gc
import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import joblib
import numpy as np
import pandas as pd

from sklearn.calibration import calibration_curve
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
    StackingClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV

# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------
log = logging.getLogger("train_model_v2")
log.setLevel(logging.DEBUG)

os.makedirs("models", exist_ok=True)
fh = logging.FileHandler("models/train_model_v2.log", encoding="utf-8")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S"))

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S"))

log.handlers.clear()
log.addHandler(fh)
log.addHandler(ch)

# ---------------------------------------------------------------------------
# CONSTANTES
# ---------------------------------------------------------------------------
TARGET_FEATURES = [
    "height_diff",
    "weight_diff",
    "reach_diff",
    "splm_diff",
    "sapm_diff",
    "td_def_diff",
    "td_avg_diff",
    "sub_avg_diff",
    "str_acc_diff",
    "td_acc_diff",
    "win_rate_diff",
    "experience_diff",
    "finish_rate_diff",
    "kd_avg_diff",
    "ctrl_time_diff",
    "reach_td_def",
    "age_experience",
    "wins_diff",
    "losses_diff",
    "age_diff",
    "is_opposite_stance",
]

REQUIRED_CSV_COLUMNS = [
    "r_id", "b_id", "winner_id", "date",
    "r_sig_str_landed", "b_sig_str_landed",
    "r_sig_str_atmpted", "b_sig_str_atmpted",
    "r_td_landed", "b_td_landed",
    "r_td_atmpted", "b_td_atmpted",
    "r_sub_att", "b_sub_att",
    "r_kd", "b_kd",
    "r_ctrl", "b_ctrl",
    "method",
    "match_time_sec", "finish_round",
]


@dataclass
class ModelCard:
    model_type: str = ""
    train_date: str = ""
    dataset_rows: int = 0
    train_samples: int = 0
    test_samples: int = 0
    features: list = None
    n_features: int = 0
    best_params: dict = None
    metrics: dict = None
    feature_importances: dict = None
    cv_scores_mean: float = 0.0
    cv_scores_std: float = 0.0
    training_time_seconds: float = 0.0
    script_version: str = "4.0.0"


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def safe_val(val):
    try:
        return float(val) if pd.notna(val) else 0.0
    except (ValueError, TypeError):
        return 0.0


def parse_ufc_measurement(val):
    """Converte medidas UFC para polegadas. Suporta: 5' 8\", 68\", 135 lbs., 180 cm, números puros."""
    if pd.isna(val) or str(val).strip() in ("", "--"):
        return 0.0
    s = str(val).lower().strip()
    nums = re.findall(r"\d+\.?\d*", s)
    if not nums:
        return 0.0
    if "'" in s or '"' in s:
        feet = float(nums[0])
        inch = float(nums[1]) if len(nums) > 1 else 0.0
        return feet * 12.0 + inch
    if "cm" in s:
        return float(nums[0]) / 2.54
    return float(nums[0])


def calc_age(dob, ref_date):
    if pd.isna(dob) or dob == "" or dob == "--":
        return np.nan
    try:
        if isinstance(dob, str):
            for fmt in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
                try:
                    dob = datetime.strptime(dob, fmt)
                    break
                except ValueError:
                    continue
            else:
                return np.nan
        ref = ref_date if isinstance(ref_date, datetime) else pd.Timestamp(ref_date).to_pydatetime()
        return (ref - dob).days / 365.25
    except Exception:
        return np.nan


def parse_time_to_seconds(val):
    if pd.isna(val) or val in ("", "--"):
        return 0.0
    s = str(val)
    if ":" in s:
        try:
            parts = s.split(":")
            return int(parts[0]) * 60 + int(parts[1])
        except (ValueError, IndexError):
            return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


# ---------------------------------------------------------------------------
# TIME-SERIES FEATURE BUILDER
# ---------------------------------------------------------------------------
def build_time_series_features(df: pd.DataFrame, min_fighter_fights: int = 1) -> pd.DataFrame:
    log.info("Construindo features cronológicas V2 (Time-Series, Zero Data Leakage)...")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["r_id"] = df["r_id"].astype(str)
    df["b_id"] = df["b_id"].astype(str)
    df["winner_id"] = df["winner_id"].astype(str)
    df = df.dropna(subset=["date", "r_id", "b_id", "winner_id"])
    df = df.sort_values("date", ascending=True).reset_index(drop=True)

    total = len(df)
    log.info("  %d lutas carregadas e ordenadas", total)

    fighter_state: dict = {}

    def _init_state() -> dict:
        return {
            "fights": 0, "wins": 0, "losses": 0,
            "total_time_min": 0.0,
            "sig_str_landed": 0.0, "sig_str_atmpted": 0.0, "sig_str_absorbed": 0.0,
            "td_landed": 0.0, "td_atmpted": 0.0, "sub_att": 0.0,
            "opp_td_landed": 0.0, "opp_td_atmpted": 0.0,
            "ctrl_seconds": 0.0,
            "kd_landed": 0.0,
            "ko_wins": 0, "submission_wins": 0,
        }

    def _calc_stats(st: dict) -> dict:
        mins = max(st["total_time_min"], 1.0)
        fights = max(st["fights"], 1.0)
        str_att = max(st["sig_str_atmpted"], 1.0)
        opp_td_att = max(st["opp_td_atmpted"], 1.0)
        td_att = max(st["td_atmpted"], 1.0)
        td_val = (
            (1.0 - (st["opp_td_landed"] / opp_td_att)) * 100.0
            if st["opp_td_atmpted"] > 0
            else 50.0
        )
        total_wins = max(st["wins"], 0)
        return {
            "splm": st["sig_str_landed"] / mins,
            "sapm": st["sig_str_absorbed"] / mins,
            "str_acc": (st["sig_str_landed"] / str_att) * 100.0,
            "td_avg": st["td_landed"] / fights,
            "sub_avg": st["sub_att"] / fights,
            "td_def": td_val,
            "td_acc": (st["td_landed"] / td_att) * 100.0 if st["td_atmpted"] > 0 else 50.0,
            "win_rate": (total_wins / fights) * 100.0,
            "experience": float(st["fights"]),
            "finish_rate": ((st["ko_wins"] + st["submission_wins"]) / max(total_wins, 1)) * 100.0,
            "kd_avg": st["kd_landed"] / fights,
            "ctrl_avg": st["ctrl_seconds"] / mins,
        }

    rows: List[dict] = []
    skipped_na = 0

    for idx, row in enumerate(df.itertuples(index=False)):
        if idx % 10000 == 0:
            log.info("  Processando luta %d/%d (%.0f%%)", idx, total, idx / total * 100)

        r_id = getattr(row, "r_id", "")
        b_id = getattr(row, "b_id", "")
        winner_id = getattr(row, "winner_id", "")
        fight_date = getattr(row, "date", None)

        if not r_id or not b_id or not winner_id:
            skipped_na += 1
            continue

        target = 1 if winner_id == r_id else 0

        for fid in (r_id, b_id):
            if fid not in fighter_state:
                fighter_state[fid] = _init_state()

        r = fighter_state[r_id]
        b = fighter_state[b_id]

        r_stats = _calc_stats(r)
        b_stats = _calc_stats(b)

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
            "td_acc_diff": r_stats["td_acc"] - b_stats["td_acc"],
            "win_rate_diff": r_stats["win_rate"] - b_stats["win_rate"],
            "experience_diff": r_stats["experience"] - b_stats["experience"],
            "finish_rate_diff": r_stats["finish_rate"] - b_stats["finish_rate"],
            "kd_avg_diff": r_stats["kd_avg"] - b_stats["kd_avg"],
            "ctrl_time_diff": r_stats["ctrl_avg"] - b_stats["ctrl_avg"],
            "reach_td_def": 0.0,
            "age_experience": 0.0,
            "wins_diff": float(r["wins"]) - float(b["wins"]),
            "losses_diff": float(r["losses"]) - float(b["losses"]),
            "target": target,
        })

        # Atualizar estado pós-luta
        match_time_sec = safe_val(getattr(row, "match_time_sec", 0))
        if match_time_sec == 0:
            match_time_sec = safe_val(getattr(row, "finish_round", 1)) * 300.0
        match_time_min = match_time_sec / 60.0

        r_str_landed = safe_val(getattr(row, "r_sig_str_landed"))
        b_str_landed = safe_val(getattr(row, "b_sig_str_landed"))
        r_td_landed = safe_val(getattr(row, "r_td_landed"))
        b_td_landed = safe_val(getattr(row, "b_td_landed"))
        r_td_att = safe_val(getattr(row, "r_td_atmpted"))
        b_td_att = safe_val(getattr(row, "b_td_atmpted"))
        r_kd = safe_val(getattr(row, "r_kd"))
        b_kd = safe_val(getattr(row, "b_kd"))
        r_ctrl = parse_time_to_seconds(getattr(row, "r_ctrl", 0))
        b_ctrl = parse_time_to_seconds(getattr(row, "b_ctrl", 0))
        method = str(getattr(row, "method", "") or "").lower()

        # Red
        r["fights"] += 1
        r["total_time_min"] += match_time_min
        r["sig_str_landed"] += r_str_landed
        r["sig_str_atmpted"] += safe_val(getattr(row, "r_sig_str_atmpted"))
        r["sig_str_absorbed"] += b_str_landed
        r["td_landed"] += r_td_landed
        r["td_atmpted"] += r_td_att
        r["sub_att"] += safe_val(getattr(row, "r_sub_att"))
        r["opp_td_landed"] += b_td_landed
        r["opp_td_atmpted"] += b_td_att
        r["kd_landed"] += r_kd
        r["ctrl_seconds"] += r_ctrl
        if target == 1:
            r["wins"] += 1
            if "ko" in method or "tko" in method:
                r["ko_wins"] += 1
            elif "submission" in method:
                r["submission_wins"] += 1
        else:
            r["losses"] += 1

        # Blue
        b["fights"] += 1
        b["total_time_min"] += match_time_min
        b["sig_str_landed"] += b_str_landed
        b["sig_str_atmpted"] += safe_val(getattr(row, "b_sig_str_atmpted"))
        b["sig_str_absorbed"] += r_str_landed
        b["td_landed"] += b_td_landed
        b["td_atmpted"] += b_td_att
        b["sub_att"] += safe_val(getattr(row, "b_sub_att"))
        b["opp_td_landed"] += r_td_landed
        b["opp_td_atmpted"] += r_td_att
        b["kd_landed"] += b_kd
        b["ctrl_seconds"] += b_ctrl
        if target == 0:
            b["wins"] += 1
            if "ko" in method or "tko" in method:
                b["ko_wins"] += 1
            elif "submission" in method:
                b["submission_wins"] += 1
        else:
            b["losses"] += 1

    if skipped_na:
        log.warning("  %d lutas ignoradas (IDs ausentes)", skipped_na)

    result = pd.DataFrame(rows)

    if min_fighter_fights > 1:
        trainable = set()
        for fid, st in fighter_state.items():
            if st["fights"] >= min_fighter_fights:
                trainable.add(fid)
        before = len(result)
        result = result[result["r_id"].isin(trainable) & result["b_id"].isin(trainable)]
        log.info("  Filtro min_fights=%d: %d -> %d lutas", min_fighter_fights, before, len(result))

    log.info("  Features cronológicas construídas: %d lutas", len(result))
    del fighter_state
    gc.collect()
    return result


def enrich_with_physical_data(training_df: pd.DataFrame, details_path: Path) -> pd.DataFrame:
    if not details_path.exists():
        log.warning("fighter_details.csv não encontrado — features estáticas zeradas")
        return training_df

    try:
        details = pd.read_csv(details_path)
    except Exception as e:
        log.warning("Erro ao ler fighter_details.csv: %s", e)
        return training_df

    log.info("Enriquecendo com dados físicos, idade e stance...")

    id_col = "fighter_id" if "fighter_id" in details.columns else "id"
    if id_col not in details.columns:
        log.warning("Coluna de ID não encontrada em fighter_details.csv")
        return training_df

    static_data: dict = {}
    for row in details.itertuples(index=False):
        fid = getattr(row, id_col, np.nan)
        if pd.notna(fid):
            static_data[str(fid)] = {
                "height": parse_ufc_measurement(getattr(row, "height", 0)),
                "weight": parse_ufc_measurement(getattr(row, "weight", 0)),
                "reach": parse_ufc_measurement(getattr(row, "reach", 0)),
                "stance": str(getattr(row, "stance", "")).lower().strip(),
                "dob": getattr(row, "dob", np.nan),
            }

    h_diffs, w_diffs, r_diffs = [], [], []
    age_diffs, stance_matchups = [], []
    reach_td_defs, age_exps = [], []

    for row in training_df.itertuples(index=False):
        r_id = str(getattr(row, "r_id", ""))
        b_id = str(getattr(row, "b_id", ""))

        rd = static_data.get(r_id, {})
        bd = static_data.get(b_id, {})

        rh = rd.get("height", 0.0)
        bh = bd.get("height", 0.0)
        rr = rd.get("reach", 0.0)
        br = bd.get("reach", 0.0)

        h_diffs.append(rh - bh)
        w_diffs.append(rd.get("weight", 0.0) - bd.get("weight", 0.0))
        r_diffs.append(rr - br)

        r_age = calc_age(rd.get("dob"), getattr(row, "fight_date", None))
        b_age = calc_age(bd.get("dob"), getattr(row, "fight_date", None))
        age_diff = (r_age - b_age) if (pd.notna(r_age) and pd.notna(b_age)) else 0.0
        age_diffs.append(age_diff)

        r_stance = rd.get("stance", "")
        b_stance = bd.get("stance", "")
        stance_matchups.append(
            1 if (r_stance and b_stance and r_stance not in ("--", "") and r_stance != b_stance) else 0
        )

        td_def_diff = getattr(row, "td_def_diff", 0.0)
        reach_td_defs.append((rr - br) * td_def_diff / 100.0)

        exp_diff = getattr(row, "experience_diff", 0.0)
        age_exps.append(age_diff * exp_diff / 100.0)

    training_df["height_diff"] = h_diffs
    training_df["weight_diff"] = w_diffs
    training_df["reach_diff"] = r_diffs
    training_df["age_diff"] = age_diffs
    training_df["is_opposite_stance"] = stance_matchups
    training_df["reach_td_def"] = reach_td_defs
    training_df["age_experience"] = age_exps

    log.info("  Features estáticas + interativas anexadas: %d lutas", len(training_df))
    del static_data
    gc.collect()
    return training_df


# ---------------------------------------------------------------------------
# MODEL TRAINING
# ---------------------------------------------------------------------------
def train_stacking_ensemble(
    X_train: np.ndarray, y_train: np.ndarray,
    X_test: np.ndarray, y_test: np.ndarray,
    quick: bool = False,
) -> Tuple[StackingClassifier, dict]:
    n_iter = 5 if quick else 20
    cv_folds = 3 if quick else 5

    base_models = [
        ("rf", RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=5, class_weight="balanced", random_state=42, n_jobs=-1)),
        ("hgb", HistGradientBoostingClassifier(max_iter=150, max_depth=5, learning_rate=0.05, random_state=42)),
    ]

    log.info("Treinando Stacking Ensemble (RF + HGB → LogisticRegression)...")
    t0 = time.time()

    rf_grid = {
        "n_estimators": [100, 200, 300],
        "max_depth": [5, 8, 10, 15],
        "min_samples_leaf": [3, 5, 10],
        "class_weight": ["balanced", "balanced_subsample", None],
    }
    hgb_grid = {
        "max_iter": [100, 150, 200],
        "max_depth": [3, 5, 7, None],
        "learning_rate": [0.02, 0.05, 0.1],
        "l2_regularization": [0.0, 0.5, 1.0],
    }

    log.info("  🔍 Tuning RandomForest...")
    rf_search = RandomizedSearchCV(
        RandomForestClassifier(random_state=42, n_jobs=-1),
        rf_grid, n_iter=n_iter, cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42),
        scoring="accuracy", n_jobs=-1, random_state=42,
    )
    rf_search.fit(X_train, y_train)
    log.info("  ✅ RF best CV: %.4f | %s", rf_search.best_score_, rf_search.best_params_)

    log.info("  🔍 Tuning HistGradientBoosting...")
    hgb_search = RandomizedSearchCV(
        HistGradientBoostingClassifier(random_state=42),
        hgb_grid, n_iter=n_iter, cv=StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42),
        scoring="accuracy", n_jobs=-1, random_state=42,
    )
    hgb_search.fit(X_train, y_train)
    log.info("  ✅ HGB best CV: %.4f | %s", hgb_search.best_score_, hgb_search.best_params_)

    stack = StackingClassifier(
        estimators=[
            ("rf", rf_search.best_estimator_),
            ("hgb", hgb_search.best_estimator_),
        ],
        final_estimator=LogisticRegression(max_iter=1000, random_state=42),
        cv=5,
        n_jobs=-1,
    )
    stack.fit(X_train, y_train)

    elapsed = time.time() - t0

    y_pred = stack.predict(X_test)
    y_proba = stack.predict_proba(X_test)[:, 1]
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_proba)

    prob_true, prob_pred = calibration_curve(y_test, y_proba, n_bins=10)
    ece = np.mean(np.abs(prob_true - prob_pred))

    log.info("  📊 Test Accuracy=%.4f | F1=%.4f | ROC-AUC=%.4f | ECE=%.4f", acc, f1, roc, ece)
    log.info("  ⏱️  Tempo de treino: %.1f segundos", elapsed)

    metrics = {
        "accuracy": float(acc), "f1_score": float(f1),
        "precision": float(prec), "recall": float(rec),
        "roc_auc": float(roc), "ece": float(ece),
        "cv_rf_mean": float(rf_search.best_score_),
        "cv_hgb_mean": float(hgb_search.best_score_),
    }

    best_params = {
        "rf": rf_search.best_params_,
        "hgb": hgb_search.best_params_,
        "final_estimator": "LogisticRegression",
    }

    return stack, metrics, best_params, elapsed


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Treinamento V2 — Stacking Ensemble")
    parser.add_argument("--quick", action="store_true", help="Modo rápido (menos tuning)")
    parser.add_argument("--dataset", default="datasets/UFC.csv", help="Caminho do CSV")
    parser.add_argument("--details", default="datasets/fighter_details.csv", help="Caminho fighter_details.csv")
    parser.add_argument("--output", default="models/mma_model_v2.joblib", help="Arquivo de saída")
    parser.add_argument("--test-size", type=float, default=0.2, help="Proporção de teste")
    args = parser.parse_args()

    log.info("=" * 80)
    log.info("🤖 TREINAMENTO DO MODELO MMA V2 — STACKING ENSEMBLE v4.0")
    log.info("=" * 80)
    log.info("Dataset:     %s", os.path.abspath(args.dataset))
    log.info("Detalhes:    %s", os.path.abspath(args.details))
    log.info("Output:      %s", os.path.abspath(args.output))
    log.info("Tuning:      %s", "✅ (quick)" if args.quick else "✅")
    log.info("Test size:   %.0f%%", args.test_size * 100)

    # 1. Carregar dados
    log.info("📥 Passo 1: Carregando dados...")
    df = pd.read_csv(args.dataset)
    log.info("  %d linhas carregadas (%d colunas)", len(df), len(df.columns))

    # Validar
    log.info("🔍 Validando dados de entrada...")
    missing = [c for c in REQUIRED_CSV_COLUMNS if c not in df.columns]
    if missing:
        log.error("❌ Colunas ausentes: %s", missing)
        sys.exit(1)
    na_before = len(df)
    df = df.dropna(subset=["r_id", "b_id", "winner_id", "date"])
    log.info("  ⚠️  %d linhas removidas por IDs/data ausentes", na_before - len(df))

    # 2. Features cronológicas
    log.info("🔧 Passo 2: Construindo features cronológicas V2...")
    training_df = build_time_series_features(df)

    # 3. Enriquecer com dados físicos + interações
    log.info("📏 Enriquecendo com dados físicos + interações...")
    training_df = enrich_with_physical_data(training_df, Path(args.details))
    log.info("  Total de lutas processadas: %d", len(training_df))

    # 4. Split treino/teste
    log.info("📊 Passo 3: Preparando matrizes de treino/teste...")
    from sklearn.model_selection import train_test_split

    X = training_df[TARGET_FEATURES].fillna(0)
    y = training_df["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42, stratify=y
    )
    log.info("  Amostras: Treino=%d | Teste=%d", len(X_train), len(X_test))
    log.info("  Treino: Red=%.1f%%  Blue=%.1f%%", y_train.mean() * 100, (1 - y_train.mean()) * 100)
    log.info("  Teste: Red=%.1f%%  Blue=%.1f%%", y_test.mean() * 100, (1 - y_test.mean()) * 100)

    # Correlação
    log.info("📊 Análise de correlação feature↔target:")
    for col in TARGET_FEATURES:
        corr = training_df[col].corr(training_df["target"])
        if pd.isna(corr):
            log.info("  %-24s   NaN (sem variância)", col)
        else:
            bar = "█" * max(0, int(abs(corr) * 50))
            log.info("  %-24s %+7.4f %s", col, corr, bar)

    # Warn high correlations
    corr_matrix = training_df[TARGET_FEATURES].corr()
    high_corr = []
    for i in range(len(TARGET_FEATURES)):
        for j in range(i + 1, len(TARGET_FEATURES)):
            if abs(corr_matrix.iloc[i, j]) > 0.85:
                high_corr.append(f"{TARGET_FEATURES[i]} ↔ {TARGET_FEATURES[j]} : {corr_matrix.iloc[i, j]:.4f}")
    if high_corr:
        log.warning("⚠️  Pares altamente correlacionados (>0.85):")
        for pair in high_corr:
            log.warning("  %s", pair)

    # 5. Treinar stacking ensemble
    log.info("🏋️ Passo 4: Treinando Stacking Ensemble...")
    model, metrics, best_params, train_time = train_stacking_ensemble(
        X_train.values, y_train.values, X_test.values, y_test.values, args.quick
    )

    # Classification report
    y_pred = model.predict(X_test.values)
    log.info("📋 Classification Report:\n%s", classification_report(y_test, y_pred, target_names=["Blue Vence", "Red Vence"]))

    cm = confusion_matrix(y_test, y_pred)
    log.info("📋 Confusion Matrix:\n  [[%d, %d], [%d, %d]]", cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1])

    # Feature importances (from RF in ensemble)
    log.info("📊 Importância das Features (RandomForest):")
    rf_model = model.named_estimators_["rf"]
    importances = rf_model.feature_importances_
    for feat, imp in sorted(zip(TARGET_FEATURES, importances), key=lambda x: -x[1]):
        bar = "█" * max(0, int(imp * 100))
        log.info("  %-24s %.6f %s", feat, imp, bar)

    # 6. Salvar
    log.info("💾 Passo 5: Salvando modelo e Model Card...")
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    joblib.dump(model, args.output, compress=3)
    log.info("  ✅ Modelo salvo: %s", os.path.abspath(args.output))

    card = ModelCard(
        model_type="StackingEnsemble(RF+HGB→LR)",
        train_date=datetime.now(timezone.utc).isoformat(),
        dataset_rows=len(df),
        train_samples=len(X_train),
        test_samples=len(X_test),
        features=TARGET_FEATURES,
        n_features=len(TARGET_FEATURES),
        best_params=best_params,
        metrics=metrics,
        training_time_seconds=round(train_time, 2),
    )
    metadata_path = args.output.replace(".joblib", "_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(asdict(card), f, indent=2, ensure_ascii=False)
    log.info("  ✅ Model Card salvo: %s", os.path.abspath(metadata_path))

    # Validar compatibilidade
    loaded = joblib.load(args.output)
    n_feat = loaded.n_features_in_ if hasattr(loaded, "n_features_in_") else len(TARGET_FEATURES)
    if n_feat == len(TARGET_FEATURES):
        log.info("✅ Modelo compatível: %d features confirmadas", n_feat)
    else:
        log.error("❌ Incompatibilidade: modelo %d vs features %d", n_feat, len(TARGET_FEATURES))

    log.info("🎉 PIPELINE V2 CONCLUÍDO COM SUCESSO!")
    log.info("   Modelo:   %s", os.path.abspath(args.output))
    log.info("   Metadados: %s", os.path.abspath(metadata_path))


if __name__ == "__main__":
    main()
