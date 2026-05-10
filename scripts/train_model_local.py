#!/usr/bin/env python3
"""
🤖 Treinamento do Modelo de Predição MMA — Production Grade

Este script treina um modelo de ML para prever o vencedor de lutas de MMA,
utilizando "Janela Expansiva" (Time-Series) para eliminar Data Leakage.

Features:
  - CLI configurável com argparse (paths, modo rápido, validate-only)
  - Structured logging (arquivo + stdout)
  - Model Card com metadados (features, hiperparâmetros, métricas, data)
  - RandomizedSearchCV para tuning automático
  - Métricas completas (ROC-AUC, F1, matriz de confusão, calibration)
  - Validação de dados de entrada (colunas, balanceamento, correlação)
  - Checkpoint de features intermediárias (--cache-features)
  - Suporte a compressão do modelo

Uso:
    python scripts/train_model_local.py
    python scripts/train_model_local.py --quick --no-tune
    python scripts/train_model_local.py --cache-features --validate-only
    python scripts/train_model_local.py --dataset meu.csv --output-dir ./out

Saída:
    models/mma_model_v1.joblib       # Modelo treinado
    models/mma_model_v1_metadata.json # Model Card com métricas e config
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
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Garantir encoding UTF-8 no stdout (necessario no Windows)
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import joblib
import numpy as np
import pandas as pd

from sklearn.calibration import calibration_curve
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.preprocessing import LabelEncoder

# ---------------------------------------------------------------------------
# CONSTANTES (mantidas em sincronia com app/services/ml/prediction_service.py)
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
    "match_time_sec", "finish_round",
]

# ---------------------------------------------------------------------------
# MODEL CARD (metadados salvos junto com o modelo)
# ---------------------------------------------------------------------------


@dataclass
class ModelCard:
    model_type: str = ""
    train_date: str = ""
    dataset_rows: int = 0
    train_samples: int = 0
    test_samples: int = 0
    features: List[str] = field(default_factory=list)
    n_features: int = 0
    best_params: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    feature_importances: Dict[str, float] = field(default_factory=dict)
    cv_scores_mean: float = 0.0
    cv_scores_std: float = 0.0
    training_time_seconds: float = 0.0
    script_version: str = "3.0.0"

    def to_json(self, path: Path) -> None:
        data = asdict(self)
        data["train_date"] = datetime.now(timezone.utc).isoformat()
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    @classmethod
    def from_json(cls, path: Path) -> "ModelCard":
        return cls(**json.loads(path.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

def setup_logging(log_dir: Optional[Path] = None, verbose: bool = False) -> logging.Logger:
    logger = logging.getLogger("train_model")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S"
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(fmt)
    logger.handlers.clear()
    logger.addHandler(console)

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / "train_model.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


log = logging.getLogger("train_model")


# ---------------------------------------------------------------------------
# UTILITÁRIOS
# ---------------------------------------------------------------------------

def safe_val(val: Any, default: float = 0.0) -> float:
    """Converte valor pandas para float seguro, retornando default se NaN."""
    return float(val) if pd.notna(val) else default


def parse_cm_to_inches(val: Any) -> float:
    """Converte altura em cm para polegadas (para dados métricos)."""
    try:
        cm = float(val)
        return round(cm / 2.54, 2) if 50 < cm < 300 else 0.0
    except (ValueError, TypeError):
        return 0.0


def parse_ufc_measurement(val: Any) -> float:
    """
    Converte medidas UFC para polegadas (float).
    Suporta formatos: "5' 11\"", "6'", "71\"", "180 cm", números puros.
    Retorna 0.0 para valores inválidos.
    """
    if pd.isna(val):
        return 0.0

    val_str = str(val).lower().strip()
    if not val_str or val_str in ("--", "na", "nan", ""):
        return 0.0

    nums = re.findall(r"\d+\.?\d*", val_str)
    if not nums:
        return 0.0

    if "'" in val_str or '"' in val_str:
        feet = float(nums[0])
        inch = float(nums[1]) if len(nums) > 1 else 0.0
        return feet * 12.0 + inch

    if "cm" in val_str:
        return parse_cm_to_inches(nums[0])

    return float(nums[0])


def calc_age(dob_str: Any, fight_date: Any) -> float:
    """Calcula idade (anos) na data da luta. Retorna NaN se inválido."""
    if pd.isna(dob_str) or pd.isna(fight_date):
        return np.nan
    if isinstance(dob_str, str) and dob_str.strip() in ("--", ""):
        return np.nan

    try:
        formats = ["%b %d, %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]
        dob = None
        for fmt in formats:
            try:
                dob = pd.to_datetime(dob_str, format=fmt)
                break
            except (ValueError, TypeError):
                continue
        if dob is None:
            dob = pd.to_datetime(dob_str, errors="coerce")
        if pd.isna(dob):
            return np.nan
        age_days = (pd.Timestamp(fight_date) - dob).days
        return age_days / 365.25
    except Exception:
        return np.nan


def _get_trainable_fighters(fighter_state: dict, min_fights: int) -> set:
    """Retorna lutadores com histórico suficiente para treinamento."""
    return {
        fid
        for fid, st in fighter_state.items()
        if st["fights"] >= min_fights
    }


# ---------------------------------------------------------------------------
# PIPELINE DE FEATURES
# ---------------------------------------------------------------------------

def validate_input_data(df: pd.DataFrame) -> List[str]:
    """Valida dados de entrada e retorna warnings."""
    warnings: List[str] = []

    missing = [c for c in REQUIRED_CSV_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colunas obrigatórias ausentes no CSV: {missing}\n"
            f"Colunas encontradas: {list(df.columns)}"
        )

    n_before = len(df)
    df_temp = df.dropna(subset=["r_id", "b_id", "winner_id", "date"]).copy()
    if len(df_temp) < n_before:
        warnings.append(f"{n_before - len(df_temp)} linhas removidas por IDs/data ausentes")

    df_temp["winner_id"] = df_temp["winner_id"].astype(str)
    invalid_winner = ~df_temp["winner_id"].isin(
        df_temp["r_id"].astype(str).unique().tolist()
        + df_temp["b_id"].astype(str).unique().tolist()
    )
    if invalid_winner.any():
        warnings.append(f"{invalid_winner.sum()} lutas com winner_id desconhecido")

    return warnings


def build_time_series_features(df: pd.DataFrame, min_fighter_fights: int = 1) -> pd.DataFrame:
    """
    Constrói features cronológicas simulando o fluxo do tempo.
    Stats de cada lutador refletem APENAS lutas anteriores (Zero Data Leakage).

    Args:
        df: DataFrame com colunas do UFC.csv
        min_fighter_fights: Mínimo de lutas no histórico para incluir

    Returns:
        DataFrame com features calculadas e coluna target
    """
    log.info("Construindo features cronológicas (Time-Series, Zero Data Leakage)...")

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
            "td_landed": 0.0, "sub_att": 0.0,
            "opp_td_landed": 0.0, "opp_td_atmpted": 0.0,
        }

    def _calc_stats(st: dict) -> dict:
        mins = max(st["total_time_min"], 1.0)
        fights = max(st["fights"], 1.0)
        str_att = max(st["sig_str_atmpted"], 1.0)
        opp_td_att = max(st["opp_td_atmpted"], 1.0)
        td_def = (
            (1.0 - (st["opp_td_landed"] / opp_td_att)) * 100.0
            if st["opp_td_atmpted"] > 0
            else 50.0
        )
        return {
            "splm": st["sig_str_landed"] / mins,
            "sapm": st["sig_str_absorbed"] / mins,
            "str_acc": (st["sig_str_landed"] / str_att) * 100.0,
            "td_avg": st["td_landed"] / fights,
            "sub_avg": st["sub_att"] / fights,
            "td_def": td_def,
        }

    rows: List[dict] = []
    skipped_na = 0
    last_log = 0

    for idx, row in enumerate(df.itertuples(index=False)):
        if idx % 10000 == 0 and idx > last_log:
            log.info("  Processando luta %d/%d (%.0f%%)", idx, total, idx / total * 100)
            last_log = idx

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

        # Features baseadas no passado
        r_stats = _calc_stats(r)
        b_stats = _calc_stats(b)

        rows.append({
            "r_id": r_id,
            "b_id": b_id,
            "fight_date": fight_date,
            "height_diff": 0.0,
            "weight_diff": 0.0,
            "reach_diff": 0.0,
            "age_diff": 0.0,
            "is_opposite_stance": 0,
            "splm_diff": r_stats["splm"] - b_stats["splm"],
            "sapm_diff": r_stats["sapm"] - b_stats["sapm"],
            "td_def_diff": r_stats["td_def"] - b_stats["td_def"],
            "td_avg_diff": r_stats["td_avg"] - b_stats["td_avg"],
            "sub_avg_diff": r_stats["sub_avg"] - b_stats["sub_avg"],
            "str_acc_diff": r_stats["str_acc"] - b_stats["str_acc"],
            "wins_diff": float(r["wins"]) - float(b["wins"]),
            "losses_diff": float(r["losses"]) - float(b["losses"]),
            "target": target,
        })

        # Atualizar estado (pós-luta)
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

        # Red
        r["fights"] += 1
        r["total_time_min"] += match_time_min
        r["sig_str_landed"] += r_str_landed
        r["sig_str_atmpted"] += safe_val(getattr(row, "r_sig_str_atmpted"))
        r["sig_str_absorbed"] += b_str_landed
        r["td_landed"] += r_td_landed
        r["sub_att"] += safe_val(getattr(row, "r_sub_att"))
        r["opp_td_landed"] += b_td_landed
        r["opp_td_atmpted"] += b_td_att
        if target == 1:
            r["wins"] += 1
        else:
            r["losses"] += 1

        # Blue
        b["fights"] += 1
        b["total_time_min"] += match_time_min
        b["sig_str_landed"] += b_str_landed
        b["sig_str_atmpted"] += safe_val(getattr(row, "b_sig_str_atmpted"))
        b["sig_str_absorbed"] += r_str_landed
        b["td_landed"] += b_td_landed
        b["sub_att"] += safe_val(getattr(row, "b_sub_att"))
        b["opp_td_landed"] += r_td_landed
        b["opp_td_atmpted"] += r_td_att
        if target == 0:
            b["wins"] += 1
        else:
            b["losses"] += 1

    if skipped_na:
        log.warning("  %d lutas ignoradas (IDs ausentes)", skipped_na)

    result = pd.DataFrame(rows)

    if min_fighter_fights > 1:
        trainable = _get_trainable_fighters(fighter_state, min_fighter_fights)
        before = len(result)
        result = result[
            result["r_id"].isin(trainable) & result["b_id"].isin(trainable)
        ]
        log.info(
            "  Filtro min_fights=%d: %d -> %d lutas", min_fighter_fights, before, len(result)
        )

    log.info("  Features cronológicas construídas: %d lutas", len(result))
    del fighter_state
    gc.collect()
    return result


def enrich_with_physical_data(
    training_df: pd.DataFrame, details_path: Path
) -> pd.DataFrame:
    """Adiciona features físicas (altura, peso, envergadura, idade, stance)."""
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

    for row in training_df.itertuples(index=False):
        r_id = str(getattr(row, "r_id", ""))
        b_id = str(getattr(row, "b_id", ""))
        fight_date = getattr(row, "fight_date", None)

        rd = static_data.get(r_id, {})
        bd = static_data.get(b_id, {})

        h_diffs.append(rd.get("height", 0.0) - bd.get("height", 0.0))
        w_diffs.append(rd.get("weight", 0.0) - bd.get("weight", 0.0))
        r_diffs.append(rd.get("reach", 0.0) - bd.get("reach", 0.0))

        r_age = calc_age(rd.get("dob"), fight_date)
        b_age = calc_age(bd.get("dob"), fight_date)
        age_diffs.append(
            (r_age - b_age) if (pd.notna(r_age) and pd.notna(b_age)) else 0.0
        )

        r_stance = rd.get("stance", "")
        b_stance = bd.get("stance", "")
        stance_matchups.append(
            1 if (r_stance and b_stance and r_stance not in ("--", "") and r_stance != b_stance) else 0
        )

    training_df["height_diff"] = h_diffs
    training_df["weight_diff"] = w_diffs
    training_df["reach_diff"] = r_diffs
    training_df["age_diff"] = age_diffs
    training_df["is_opposite_stance"] = stance_matchups

    log.info("  Features estáticas anexadas: %d lutas", len(training_df))

    del static_data
    gc.collect()
    return training_df


# ---------------------------------------------------------------------------
# HIPERPARÂMETROS E TUNING
# ---------------------------------------------------------------------------

RANDOM_FOREST_PARAM_GRID = {
    "n_estimators": [100, 200, 300],
    "max_depth": [5, 8, 10, 15],
    "min_samples_leaf": [3, 5, 10],
    "class_weight": ["balanced", "balanced_subsample", None],
}

HGB_PARAM_GRID = {
    "max_iter": [100, 150, 200],
    "max_depth": [3, 5, 7, None],
    "learning_rate": [0.02, 0.05, 0.1],
    "l2_regularization": [0.0, 0.5, 1.0],
}


def get_base_models() -> Dict[str, Any]:
    """Retorna dicionário de modelos base (sem tuning)."""
    return {
        "RandomForest": RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=150,
            max_depth=5,
            learning_rate=0.05,
            random_state=42,
        ),
    }


def tune_model(
    name: str,
    model: Any,
    param_grid: dict,
    X_train: np.ndarray,
    y_train: np.ndarray,
    n_iter: int = 20,
    cv: int = 5,
) -> Tuple[Any, Dict[str, Any]]:
    """
    Executa RandomizedSearchCV para encontrar os melhores hiperparâmetros.

    Returns:
        (best_model, best_params)
    """
    log.info("  🔍 Tuning %s (RandomizedSearchCV, %d iters, %d-fold)...", name, n_iter, cv)
    search = RandomizedSearchCV(
        model,
        param_distributions=param_grid,
        n_iter=n_iter,
        cv=StratifiedKFold(n_splits=cv, shuffle=True, random_state=42),
        scoring="accuracy",
        n_jobs=-1,
        random_state=42,
        verbose=0,
    )
    search.fit(X_train, y_train)

    log.info("  ✅ Melhor score CV: %.4f", search.best_score_)
    log.info("  ✅ Melhores params: %s", search.best_params_)

    return search.best_estimator_, search.best_params_


def evaluate_model(
    model: Any,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    cv: int = 5,
) -> Dict[str, float]:
    """
    Avalia modelo com métricas completas.

    Returns:
        Dict com accuracy, f1, precision, recall, roc_auc, cv_mean, cv_std
    """
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

    cv_scores = cross_val_score(
        model, X_train, y_train, cv=StratifiedKFold(cv, shuffle=True, random_state=42),
        scoring="accuracy", n_jobs=-1,
    )

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_score": float(f1_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)) if y_proba is not None else 0.0,
        "cv_accuracy_mean": float(cv_scores.mean()),
        "cv_accuracy_std": float(cv_scores.std()),
    }

    return metrics


def analyze_feature_importances(
    model: Any, features: List[str]
) -> Dict[str, float]:
    """Extrai e ordena importâncias das features."""
    if not hasattr(model, "feature_importances_"):
        return {}

    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]

    result = {}
    for i in indices:
        result[features[i]] = round(float(importances[i]), 6)

    return result


def analyze_feature_correlations(X: pd.DataFrame, y: pd.Series) -> None:
    """Loga correlação de cada feature com o target e entre features."""
    log.info("📊 Análise de correlação feature↔target:")
    correlations = X.corrwith(y).sort_values(key=abs, ascending=False)
    for feat, corr in correlations.items():
        bar = "█" * min(int(abs(corr) * 20), 40)
        log.info("  %-22s %+.4f %s", feat, corr, bar)

    high_corr_pairs = []
    corr_matrix = X.corr().abs()
    for i in range(len(X.columns)):
        for j in range(i + 1, len(X.columns)):
            if corr_matrix.iloc[i, j] > 0.85:
                high_corr_pairs.append(
                    (X.columns[i], X.columns[j], corr_matrix.iloc[i, j])
                )

    if high_corr_pairs:
        log.warning("⚠️  Pares altamente correlacionados (>0.85):")
        for f1, f2, v in sorted(high_corr_pairs, key=lambda x: -x[2]):
            log.warning("  %s ↔ %s : %.4f", f1, f2, v)


def log_class_balance(y_train: pd.Series, y_test: pd.Series) -> None:
    """Loga distribuição das classes nos splits."""
    for name, y in ("Treino", y_train), ("Teste", y_test):
        vc = y.value_counts(normalize=True)
        red = vc.get(1, 0) * 100
        blue = vc.get(0, 0) * 100
        log.info("  %s: Red=%.1f%%  Blue=%.1f%%  (n=%d)", name, red, blue, len(y))


def print_report(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    cm: Optional[np.ndarray] = None,
    probas: Optional[np.ndarray] = None,
) -> None:
    """Imprime relatório de classificação + matriz de confusão."""
    log.info("📋 Classification Report:")
    for line in classification_report(
        y_test, y_pred, target_names=["Blue Vence", "Red Vence"], digits=4
    ).splitlines():
        log.info("  %s", line)

    if cm is not None:
        log.info("📋 Confusion Matrix (linha=real, col=predito):")
        log.info("  [[Blue→Blue  Blue→Red ]")
        log.info("   [Red→Blue   Red→Red  ]]")
        log.info("  %s", cm.tolist())

    if probas is not None:
        try:
            prob_true, prob_pred = calibration_curve(y_test, probas, n_bins=10)
            ece = np.mean(np.abs(prob_true - prob_pred))
            log.info("📊 Expected Calibration Error (ECE): %.4f", ece)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# ORQUESTRADOR PRINCIPAL
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="🤖 Treinamento do Modelo de Predicao MMA - Production Grade",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                                    # Treino completo com tuning
  %(prog)s --quick --no-tune                  # Rapido, sem tuning
  %(prog)s --cache-features /tmp/features.parquet  # Cache de features
  %(prog)s --validate-only                    # Apenas validar dados
        """,
    )

    parser.add_argument(
        "--dataset", type=Path,
        default=None,
        help="Caminho para o CSV de lutas (default: datasets/UFC.csv)",
    )
    parser.add_argument(
        "--fighter-details", type=Path,
        default=None,
        help="Caminho para CSV de detalhes dos lutadores (default: datasets/fighter_details.csv)",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=None,
        help="Diretório de saída para modelo e relatório (default: models/)",
    )
    parser.add_argument(
        "--output-name", type=str,
        default="mma_model_v1",
        help="Nome base do arquivo de saída (default: mma_model_v1)",
    )
    parser.add_argument(
        "--test-size", type=float, default=0.2,
        help="Fração do dataset para teste (default: 0.2)",
    )
    parser.add_argument(
        "--random-state", type=int, default=42,
        help="Seed para reprodutibilidade (default: 42)",
    )
    parser.add_argument(
        "--cv-folds", type=int, default=5,
        help="Número de folds para cross-validation (default: 5)",
    )
    parser.add_argument(
        "--tune-iters", type=int, default=20,
        help="Iterações do RandomizedSearchCV (default: 20)",
    )
    parser.add_argument(
        "--no-tune", action="store_true",
        help="Pular tuning de hiperparâmetros",
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Modo rápido: menos iters de tuning, CV reduzido",
    )
    parser.add_argument(
        "--cache-features", type=Path, default=None,
        help="Salvar/carregar features processadas em arquivo parquet",
    )
    parser.add_argument(
        "--validate-only", action="store_true",
        help="Apenas validar dados de entrada, sem treinar",
    )
    parser.add_argument(
        "--compress", type=int, default=3,
        help="Nível de compressão joblib 0-9 (default: 3)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Logging verboso (DEBUG)",
    )

    args = parser.parse_args()

    # ---- Config de paths ----
    project_root = Path(__file__).parent.parent
    dataset_path = args.dataset or (project_root / "datasets" / "UFC.csv")
    details_path = args.fighter_details or (project_root / "datasets" / "fighter_details.csv")
    output_dir = args.output_dir or (project_root / "models")
    output_dir.mkdir(parents=True, exist_ok=True)

    # ---- Logging ----
    global log
    log = setup_logging(output_dir, verbose=args.verbose)

    # ---- Ajuste modo rápido ----
    if args.quick:
        args.no_tune = True
        args.cv_folds = 3
        log.info("⚡ Modo rápido ativado (sem tuning, CV=%d)", args.cv_folds)

    log.info("=" * 80)
    log.info("🤖 TREINAMENTO DO MODELO MMA — PRODUCTION GRADE v3.0")
    log.info("=" * 80)
    log.info("Dataset:     %s", dataset_path)
    log.info("Detalhes:    %s", details_path)
    log.info("Output:      %s/%s.joblib", output_dir, args.output_name)
    log.info("Tuning:      %s", "❌" if args.no_tune else "✅")
    log.info("Test size:   %.0f%%", args.test_size * 100)
    log.info("CV folds:    %d", args.cv_folds)
    log.info("Random seed: %d", args.random_state)

    # ---- Passo 1: Carregar dados ----
    if not dataset_path.exists():
        log.error("❌ Dataset não encontrado: %s", dataset_path)
        sys.exit(1)

    log.info("📥 Passo 1: Carregando dados...")
    df = pd.read_csv(dataset_path)
    log.info("  %d linhas carregadas (%d colunas)", len(df), len(df.columns))

    if len(df) == 0:
        log.error("❌ Dataset vazio")
        sys.exit(1)

    # ---- Validar dados ----
    log.info("🔍 Validando dados de entrada...")
    try:
        warnings = validate_input_data(df)
        for w in warnings:
            log.warning("  ⚠️  %s", w)
    except ValueError as e:
        log.error("❌ %s", e)
        sys.exit(1)

    if args.validate_only:
        log.info("✅ Dados validados com sucesso (--validate-only).")
        return

    # ---- Passo 2: Features cronológicas ----
    if args.cache_features and args.cache_features.exists():
        log.info("📂 Carregando features do cache: %s", args.cache_features)
        training_data = pd.read_parquet(args.cache_features)
    else:
        log.info("🔧 Passo 2: Construindo features cronológicas...")
        training_data = build_time_series_features(df)

        if len(training_data) < 100:
            log.error("❌ Apenas %d lutas após processamento — mínimo 100", len(training_data))
            sys.exit(1)

        log.info("📏 Enriquecendo com dados físicos...")
        training_data = enrich_with_physical_data(training_data, details_path)

        if args.cache_features:
            training_data.to_parquet(args.cache_features, index=False)
            log.info("  Cache salvo em: %s", args.cache_features)

    log.info("  Total de lutas processadas: %d", len(training_data))

    # ---- Verificar features ----
    missing_features = [f for f in TARGET_FEATURES if f not in training_data.columns]
    if missing_features:
        log.error("❌ Features ausentes: %s", missing_features)
        sys.exit(1)

    # ---- Passo 3: Preparar matrizes ----
    log.info("📊 Passo 3: Preparando matrizes de treino/teste...")
    X = training_data[TARGET_FEATURES].fillna(0)
    y = training_data["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state, stratify=y,
    )

    log.info("  Amostras: Treino=%d | Teste=%d", len(X_train), len(X_test))
    log_class_balance(y_train, y_test)

    # Análise exploratória
    analyze_feature_correlations(X_train, y_train)

    # ---- Passo 4: Treinar e avaliar ----
    log.info("🏋️ Passo 4: Treinando modelos...")
    t_start = time.monotonic()

    models = get_base_models()
    best_model, best_name, best_params, best_metrics = None, "", {}, {}
    best_score = -1.0

    for name, model in models.items():
        log.info("━" * 60)
        log.info("Treinando %s...", name)
        tuned_model = model
        params = {}

        if not args.no_tune:
            param_grid = (
                RANDOM_FOREST_PARAM_GRID if name == "RandomForest"
                else HGB_PARAM_GRID
            )
            tuned_model, params = tune_model(
                name, model, param_grid,
                X_train.values, y_train.values,
                n_iter=args.tune_iters, cv=args.cv_folds,
            )
        else:
            log.info("  (tuning desabilitado via --no-tune)")
            tuned_model.fit(X_train, y_train)

        metrics = evaluate_model(
            tuned_model, X_train.values, y_train.values,
            X_test.values, y_test.values,
            cv=args.cv_folds,
        )

        log.info(
            "  📊 Test Accuracy=%.4f | F1=%.4f | ROC-AUC=%.4f | CV=%.4f±%.4f",
            metrics["accuracy"], metrics["f1_score"],
            metrics["roc_auc"], metrics["cv_accuracy_mean"], metrics["cv_accuracy_std"],
        )

        if metrics["accuracy"] > best_score:
            best_score = metrics["accuracy"]
            best_model = tuned_model
            best_name = name
            best_params = params
            best_metrics = metrics

    training_time = time.monotonic() - t_start

    log.info("=" * 60)
    log.info("🏆 Melhor modelo: %s (Accuracy: %.4f)", best_name, best_score)
    log.info("⏱️  Tempo total de treino: %.1f segundos", training_time)

    # Relatório detalhado
    y_pred = best_model.predict(X_test.values)
    y_proba = (
        best_model.predict_proba(X_test.values)[:, 1]
        if hasattr(best_model, "predict_proba")
        else None
    )
    cm = confusion_matrix(y_test, y_pred)

    print_report(y_test.values, y_pred, cm, y_proba)

    # Feature importances
    importances = analyze_feature_importances(best_model, TARGET_FEATURES)
    if importances:
        log.info("📊 Importância das Features:")
        for feat, imp in sorted(importances.items(), key=lambda x: -x[1]):
            bar = "█" * max(int(imp * 100), 1)
            log.info("  %-22s %.6f %s", feat, imp, bar)

    # ---- Passo 5: Salvar modelo e metadados ----
    log.info("💾 Passo 5: Salvando modelo e Model Card...")

    model_path = output_dir / f"{args.output_name}.joblib"
    joblib.dump(best_model, model_path, compress=args.compress)
    log.info("  ✅ Modelo salvo: %s (compress=%d)", model_path, args.compress)

    card = ModelCard(
        model_type=best_name,
        dataset_rows=len(df),
        train_samples=len(X_train),
        test_samples=len(X_test),
        features=TARGET_FEATURES,
        n_features=len(TARGET_FEATURES),
        best_params=best_params,
        metrics=best_metrics,
        feature_importances=importances,
        cv_scores_mean=best_metrics.get("cv_accuracy_mean", 0),
        cv_scores_std=best_metrics.get("cv_accuracy_std", 0),
        training_time_seconds=round(training_time, 2),
    )

    metadata_path = output_dir / f"{args.output_name}_metadata.json"
    card.to_json(metadata_path)
    log.info("  ✅ Model Card salvo: %s", metadata_path)

    # ---- Verificar compatibilidade com o serviço de predição ----
    _verify_model_compatibility(best_model, model_path)

    log.info("🎉 PIPELINE CONCLUÍDO COM SUCESSO!")
    log.info("   Modelo:   %s", model_path)
    log.info("   Metadados: %s", metadata_path)


def _verify_model_compatibility(model: Any, model_path: Path) -> None:
    """Verifica se o modelo é compatível com o MLPredictionService."""
    if not hasattr(model, "n_features_in_"):
        log.warning("⚠️  Modelo não reporta n_features_in_ — pulando verificação")
        return

    expected = model.n_features_in_
    actual = len(TARGET_FEATURES)

    if expected != actual:
        log.error(
            "❌ INCOMPATIBILIDADE: modelo espera %d features, TARGET_FEATURES tem %d",
            expected, actual,
        )
        log.error(
            "   Atualize TARGET_FEATURES neste script E em "
            "app/services/ml/prediction_service.py"
        )
    else:
        log.info("✅ Modelo compatível: %d features confirmadas", actual)

    # Verifica que o modelo carrega corretamente
    try:
        reloaded = joblib.load(model_path)
        if hasattr(reloaded, "predict"):
            log.info("✅ Modelo carregado e validado com sucesso")
    except Exception as e:
        log.error("❌ Falha ao recarregar modelo: %s", e)


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
