# 🥊 FightBase - Quick Start Guide

## ⚡ Início Rápido (5 minutos)

### 1. Clone e Configure

```bash
cd /home/udson-rego/Documentos/estudos/fight-base/fight-base
cp .env.example .env
```

### 2. Inicie com Docker

```bash
docker-compose up --build
```

### 3. Execute Migrations

```bash
# Em outro terminal
docker-compose exec app alembic upgrade head
```

### 4. Crie Admin

```bash
docker-compose exec app python scripts/create_admin.py
```

### 5. Acesse!

- 🌐 API: http://localhost:8000
- 📚 Swagger: http://localhost:8000/swagger
- 📖 Docs: http://localhost:8000/docs

## 🎯 Teste Rápido no Swagger

### Passo 1: Fazer Login

1. Vá para `/api/v1/auth/token` no Swagger
2. Clique em "Try it out"
3. Use: `admin@mail.com` / `pass@word`
4. Execute e copie o `access_token`

### Passo 2: Autorizar

1. Clique no botão "Authorize" (cadeado no topo)
2. Cole o token
3. Clique em "Authorize"

### Passo 3: Criar Lutador

1. Vá para `POST /api/v1/fighters`
2. Clique em "Try it out"
3. Use este exemplo:

```json
{
  "name": "Jon Jones",
  "nickname": "Bones",
  "organization": "UFC",
  "weight_class": "Peso-pesado",
  "fighting_style": "All-around",
  "striking": 92,
  "grappling": 95,
  "defense": 88,
  "stamina": 90,
  "speed": 85,
  "strategy": 98,
  "wins": 27,
  "losses": 1,
  "is_real": true
}
```

4. Execute e salve o `id` retornado

### Passo 4: Criar Outro Lutador

Repita o passo 3 com:

```json
{
  "name": "Khabib Nurmagomedov",
  "nickname": "The Eagle",
  "organization": "UFC",
  "weight_class": "Peso-leve",
  "fighting_style": "Grappler",
  "striking": 78,
  "grappling": 98,
  "defense": 92,
  "stamina": 95,
  "speed": 82,
  "strategy": 96,
  "wins": 29,
  "losses": 0,
  "is_real": true
}
```

### Passo 5: Simular Luta! 🎮

1. Vá para `POST /api/v1/simulations`
2. Use os IDs dos lutadores criados:

```json
{
  "fighter1_id": "uuid-do-jon-jones",
  "fighter2_id": "uuid-do-khabib",
  "rounds": 5,
  "notes": "Superfight imaginária!"
}
```

3. Execute e veja o resultado! 🥊

## 📊 Endpoints Principais

| Método | Endpoint                        | Descrição         |
| ------ | ------------------------------- | ----------------- |
| GET    | `/api/v1/fighters`              | Lista lutadores   |
| POST   | `/api/v1/fighters`              | Cria lutador      |
| GET    | `/api/v1/fighters/rankings/top` | Top ranqueados    |
| POST   | `/api/v1/simulations`           | Simula luta       |
| GET    | `/api/v1/simulations/predict`   | Prevê resultado   |
| GET    | `/api/v1/simulations/compare`   | Compara lutadores |

## 🎓 Próximos Passos

1. ✅ Leia o [README.md](README.md) completo
2. 📚 Veja [EXEMPLOS_PRATICOS.md](docs/EXEMPLOS_PRATICOS.md)
3. 🧠 Entenda o [ALGORITMO_TECNICO.md](docs/ALGORITMO_TECNICO.md)
4. 💡 Explore [CASOS_DE_USO.md](docs/CASOS_DE_USO.md)
5. 🚀 Siga [PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md)

## 🐛 Problemas Comuns

### Erro: "Port 8000 already in use"

```bash
# Mate o processo usando a porta
sudo lsof -ti:8000 | xargs kill -9
```

### Erro: "Database connection failed"

```bash
# Verifique se o PostgreSQL está rodando
docker-compose ps
# Reinicie os containers
docker-compose down && docker-compose up
```

### Erro: "Unauthorized"

```bash
# Faça login novamente e use o token correto
# Token expira em 30 minutos (padrão)
```

## 💬 Suporte

- 📧 Issues: [GitHub Issues](https://github.com/UdsonWillams/fight-base/issues)
- 📖 Docs: Leia os arquivos na pasta `/docs`
- 💡 Ideias: Abra uma Issue com label "enhancement"

## 🎉 Pronto!

Agora você tem um sistema completo de simulação de lutas MMA rodando!

**Divirta-se criando lutadores e simulando lutas épicas! 🥊**
