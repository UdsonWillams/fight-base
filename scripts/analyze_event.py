#!/usr/bin/env python3
"""
📊 Analisador de Eventos em Lote (Batch Event Analyzer)
Lê as odds do evento, cruza com o modelo de ML e gera as recomendações de aposta.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.settings import get_settings
from app.database.models.base import Fighter
from app.services.ml.prediction_service import ml_prediction_service

# Cores do terminal
GREEN = '\033[92m'
RED = '\033[91m'
CYAN = '\033[96m'
YELLOW = '\033[93m'
RESET = '\033[0m'

class BettingQuantCalculator:
    """Calculadora embutida para gestão da banca de R$ 50"""
    def __init__(self, bankroll: float, kelly_fraction: float = 0.25):
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction

    def calculate_implied_prob(self, odd: float) -> float:
        return 1.0 / odd

    def analyze_bet(self, odd_fighter: float, model_prob: float) -> dict:
        implied_prob = self.calculate_implied_prob(odd_fighter)
        ev = (model_prob * odd_fighter) - 1.0
        
        b = odd_fighter - 1.0
        p = model_prob
        q = 1.0 - p
        kelly_pct = ((b * p - q) / b) * self.kelly_fraction if b > 0 else 0
        
        # Só aposta se tiver EV positivo E a fórmula de Kelly recomendar > 0
        is_approved = ev > 0 and kelly_pct > 0
        bet_amount = self.bankroll * kelly_pct if is_approved else 0.0

        return {
            "is_approved": is_approved,
            "ev_pct": ev * 100,
            "kelly_pct": kelly_pct * 100,
            "bet_amount": bet_amount,
            "implied_prob": implied_prob
        }

def get_fighter_by_name(session, identifier: str) -> Fighter:
    """Busca o lutador por nome ou ufcstats_id de forma síncrona"""
    # 1. Tenta busca exata por nome (case-insensitive)
    fighter = session.query(Fighter).filter(Fighter.name.ilike(identifier.strip())).first()
    if fighter:
        return fighter
    
    # 2. Tenta busca por ufcstats_id
    fighter = session.query(Fighter).filter(Fighter.ufcstats_id == identifier.strip()).first()
    if fighter:
        return fighter

    # 3. Tenta busca parcial por nome (fallback)
    return session.query(Fighter).filter(Fighter.name.ilike(f"%{identifier.strip()}%")).first()

def main():    
    print(f"{CYAN}" + "=" * 80)
    print("🤖 RELATÓRIO QUANTITATIVO DO EVENTO UFC (SYNC DATABASE)")
    print("=" * 80 + f"{RESET}\n")

    CSV_PATH = "datasets/event_odds.csv"
    BANKROLL = 50.00 # Sua banca inicial!
    
    try:
        df_odds = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        print(f"{RED}❌ Arquivo não encontrado: {CSV_PATH}{RESET}")
        print("Crie o arquivo com as colunas: r_name, b_name, r_odd, b_odd")
        sys.exit(1)

    hoje = datetime.now(timezone.utc)
    calc = BettingQuantCalculator(bankroll=BANKROLL)
    
    total_invested = 0.0
    approved_bets = []

    print(f"💵 Banca Inicial: R$ {BANKROLL:.2f}\n")

    # Conectar ao banco síncrono
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL_SYNC)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        for index, row in df_odds.iterrows():
            r_name = row['r_name']
            b_name = row['b_name']
            r_odd = float(row['r_odd'])
            b_odd = float(row['b_odd'])

            # 1. Busca no Banco de Dados
            fighter_r = get_fighter_by_name(session, r_name)
            fighter_b = get_fighter_by_name(session, b_name)

            if not fighter_r or not fighter_b:
                print(f"{YELLOW}⚠️ Luta ignorada: {r_name} ou {b_name} não encontrados no banco.{RESET}")
                continue

            # 2. Predição do ML
            prob_r = ml_prediction_service.predict_winner_from_model(fighter_r, fighter_b, event_date=hoje)
            
            if prob_r is None:
                print(f"{YELLOW}⚠️ Erro na predição de {r_name} vs {b_name}.{RESET}")
                continue
                
            prob_b = 1.0 - prob_r # A probabilidade do Azul é o complemento

            # 3. Análise Quantitativa
            analysis_r = calc.analyze_bet(r_odd, prob_r)
            analysis_b = calc.analyze_bet(b_odd, prob_b)

            # 4. Regras de Decisão
            if analysis_r["is_approved"]:
                print(f"{GREEN}✅ APOSTAR EM: {fighter_r.name} (Córner Vermelho){RESET}")
                print(f"   Odd: {r_odd} | ML Previu: {prob_r:.2%} | EV: +{analysis_r['ev_pct']:.2f}%")
                print(f"   💰 VALOR: R$ {analysis_r['bet_amount']:.2f} ({analysis_r['kelly_pct']:.2f}% da banca)\n")
                total_invested += analysis_r['bet_amount']
                approved_bets.append((fighter_r.name, r_odd, analysis_r['bet_amount']))

            elif analysis_b["is_approved"]:
                print(f"{GREEN}✅ APOSTAR EM: {fighter_b.name} (Córner Azul - ZEBRA!){RESET}")
                print(f"   Odd: {b_odd} | ML Previu: {prob_b:.2%} | EV: +{analysis_b['ev_pct']:.2f}%")
                print(f"   💰 VALOR: R$ {analysis_b['bet_amount']:.2f} ({analysis_b['kelly_pct']:.2f}% da banca)\n")
                total_invested += analysis_b['bet_amount']
                approved_bets.append((fighter_b.name, b_odd, analysis_b['bet_amount']))

            else:
                print(f"{RED}❌ NO BET: {r_name} vs {b_name}{RESET}")
                print(f"   Motivo: Nenhuma odd tem Valor Esperado Positivo (EV+). Fique de fora.\n")

    finally:
        # Fecha a conexão limpa, independente de dar erro ou não no loop
        session.close()

    # 5. Resumo da Ópera
    print(f"{CYAN}=" * 80)
    print(f"📋 RESUMO DO CARD")
    print("=" * 80 + f"{RESET}")
    print(f"Total de lutas analisadas: {len(df_odds)}")
    print(f"Apostas aprovadas: {len(approved_bets)}")
    print(f"Capital total investido: R$ {total_invested:.2f} ({(total_invested/BANKROLL)*100:.2f}% da banca)")
    print(f"Capital protegido (não apostado): R$ {BANKROLL - total_invested:.2f}")
    
    if approved_bets:
        print(f"\n🎟️  SEU BILHETE DE SÁBADO (APOSTAS SIMPLES):")
        for bet in approved_bets:
            print(f" - {bet[0]} (Odd {bet[1]}): R$ {bet[2]:.2f}")
    print("\nBoa sorte e confie na matemática! 🚀\n")

if __name__ == "__main__":
    main()
