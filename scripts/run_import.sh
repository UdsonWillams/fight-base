#!/bin/bash
# Script rápido para importar o dataset UFC

set -e

echo "🥊 IMPORTAÇÃO DO DATASET UFC"
echo "===================================="
echo ""

# Verificar arquivos CSV
echo "📋 Verificando arquivos CSV..."
if [ ! -f "fighter_details.csv" ]; then
    echo "❌ fighter_details.csv não encontrado!"
    exit 1
fi

if [ ! -f "event_details.csv" ]; then
    echo "❌ event_details.csv não encontrado!"
    exit 1
fi

if [ ! -f "fight_details.csv" ]; then
    echo "❌ fight_details.csv não encontrado!"
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
