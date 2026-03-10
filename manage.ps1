function Show-Menu {
    Write-Host "🥊 FightBase Manager - Windows Edition" -ForegroundColor Cyan
    Write-Host "--------------------------------------"
    Write-Host "1. Setup (Cria .env + Instala deps)"
    Write-Host "2. Up (Sobe Banco + Backend)"
    Write-Host "3. Down (Para tudo)"
    Write-Host "4. DB (Sobe só o Banco)"
    Write-Host "5. Server (Sobe só o Backend)"
    Write-Host "6. Migrate (Gera Migration)"
    Write-Host "7. Test (Roda Testes)"
    Write-Host "8. Clean (Reseta Tudo)"
    Write-Host "Q. Sair"
    Write-Host "--------------------------------------"
}

function Setup-Project {
    Write-Host "🔧 Iniciando setup..." -ForegroundColor Yellow
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" -Destination ".env"
        Write-Host "✅ Arquivo .env criado." -ForegroundColor Green
    } else {
        Write-Host "⚠️  Arquivo .env já existe." -ForegroundColor Yellow
    }
    pip install -r requirements.txt
    Write-Host "✅ Dependências instaladas!" -ForegroundColor Green
}

function Up-Project {
    Write-Host "⬆️  Subindo containers..." -ForegroundColor Green
    docker compose up -d database
    Start-Sleep -Seconds 5
    Write-Host "🥊 Iniciando backend..." -ForegroundColor Green
    uvicorn app.main:app --reload --host=0.0.0.0 --port=8080
}

function Down-Project {
    Write-Host "⬇️  Parando containers..." -ForegroundColor Yellow
    docker compose down
}

function Db-Only {
    docker compose up -d database
}

function Server-Only {
    uvicorn app.main:app --reload --host=0.0.0.0 --port=8080
}

function Run-Migrate {
    $msg = Read-Host "Digite a mensagem para a migration"
    if ($msg) {
        alembic revision --autogenerate -m "$msg"
        Write-Host "✅ Migration criada!" -ForegroundColor Green
    } else {
        Write-Host "❌ Mensagem obrigatória!" -ForegroundColor Red
    }
}

function Run-Tests {
    $env:PYTHONPATH="."
    pytest --cov=app --cov-report=term-missing --disable-warnings
}

function Clean-Project {
    Write-Host "🧹 Limpando tudo..." -ForegroundColor Red
    docker compose down -v
    Write-Host "✅ Ambiente limpo!" -ForegroundColor Green
}

# Loop do Menu
do {
    Show-Menu
    $input = Read-Host "Escolha uma opção"
    switch ($input) {
        "1" { Setup-Project }
        "2" { Up-Project }
        "3" { Down-Project }
        "4" { Db-Only }
        "5" { Server-Only }
        "6" { Run-Migrate }
        "7" { Run-Tests }
        "8" { Clean-Project }
        "Q" { Write-Host "Saindo..." ; break }
        "q" { Write-Host "Saindo..." ; break }
        default { Write-Host "Opção inválida" -ForegroundColor Red }
    }
    Write-Host ""
} while ($true)
