#!/bin/bash
# Script rápido para importar o dataset UFC

set -e

echo "🥊 IMPORTAÇÃO DO DATASET UFC"
echo "===================================="
echo ""

# Verificar arquivos CSV
echo "📋 Verificando arquivos CSV..."
if [ ! -f "datasets/fighter_details.csv" ]; then
    echo "❌ datasets/fighter_details.csv não encontrado! Execute primeiro: python scripts/scrape_dataset.py"
    exit 1
fi

if [ ! -f "datasets/event_details.csv" ]; then
    echo "❌ datasets/event_details.csv não encontrado! Execute primeiro: python scripts/scrape_dataset.py"
    exit 1
fi

if [ ! -f "datasets/fight_details.csv" ]; then
    echo "❌ datasets/fight_details.csv não encontrado! Execute primeiro: python scripts/scrape_dataset.py"
    exit 1
fi

echo "✅ Todos os arquivos CSV encontrados"
echo ""

# Aplicar migrations
echo "🔄 Aplicando migrations..."
alembic upgrade head
echo ""

# Executar importação
echo "📥 Iniciando importação..."
echo ""
python scripts/import_ufc_dataset.py

echo ""
echo "===================================="
echo "✅ Processo concluído!"
echo ""
echo "Para ver exemplos de consultas, execute:"
echo "  python scripts/example_ufc_queries.py"
