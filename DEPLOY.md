# FightBase — Guia de Deploy (Produção)

**URL Frontend:** `https://v0-vue-com-python.vercel.app`
**API (Swagger):** `https://fight-base-api.onrender.com/swagger`
**Data:** 16/05/2026

---

## 1. Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│  Usuário acessa: https://v0-vue-com-python.vercel.app       │
│                                                             │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │     VERCEL          │    │         RENDER              │ │
│  │  (Frontend Vue.js)  │───▶│  (Backend FastAPI Python)   │ │
│  │  Plano: Hobby (Free)│    │  Plano: Free (512MB RAM)    │ │
│  └─────────────────────┘    └──────────┬──────────────────┘ │
│                                        │                     │
│                           ┌────────────▼──────────────────┐ │
│                           │        SUPABASE               │ │
│                           │  (PostgreSQL Database)        │ │
│                           │  Plano: Free (500MB)          │ │
│                           └───────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Serviços Utilizados

| Serviço      | Função                    | Tecnologia           | Limites Free                   |
| ------------ | ------------------------- | -------------------- | ------------------------------ |
| **Vercel**   | Hospeda o frontend Vue.js | Static + CDN         | 100 GB bandwidth/mês           |
| **Render**   | Hospeda o backend FastAPI | Web Service Python 3 | 512 MB RAM, dorme após 15 min  |
| **Supabase** | Banco de dados PostgreSQL | Managed PostgreSQL   | 500 MB storage, 2 GB bandwidth |

---

## 3. Como criar o Backend no Render

### 3.1 Setup inicial

1. Acessar [render.com](https://render.com) → Sign Up com GitHub
2. Dashboard → **New + → Web Service**
3. Conectar repositório GitHub: `fight-base`

### 3.2 Configurações do Web Service

| Campo             | Valor                                              |
| ----------------- | -------------------------------------------------- |
| **Name**          | `fightbase-api`                                    |
| **Runtime**       | Python 3                                           |
| **Build Command** | `pip install -r requirements.txt`                  |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Branch**        | `main`                                             |
| **Auto-Deploy**   | Yes (ativa automaticamente ao dar push)            |

### 3.3 Environment Variables

Configurar em: Dashboard → fightbase-api → Environment

| Variável           | Descrição                                    | Como obter                             |
| ------------------ | -------------------------------------------- | -------------------------------------- |
| `APP_ENVIRONMENT`  | Modo de execução                             | `production`                           |
| `DATABASE_URL_ENV` | Conexão PostgreSQL (Supabase Session Pooler) | Ver seção 5                            |
| `SECRET_KEY`       | Chave segura para JWT tokens                 | Gere uma string aleatória longa        |
| `APP_CORS`         | URL do frontend na Vercel                    | `https://v0-vue-com-python.vercel.app` |
| `LOCAL_MODEL_PATH` | Caminho do modelo ML na raiz do repo         | `models/mma_model_v1.joblib`           |

### 3.4 Problema comum — IPv6

O Render não suporta IPv6. A conexão direta com `db.SEUHOST.supabase.co` resolve pra IPv6 e falha com `Network is unreachable`.

**Solução:** usar o **Session Pooler** do Supabase (explicado na seção 5).

---

## 4. Como criar o Frontend na Vercel

### 4.1 Setup inicial

```powershell
# Instalar Vercel CLI (Windows PowerShell)
npm install -g vercel

# Login (abre navegador)
vercel login

# Deploy (dentro da pasta fight-base/)
vercel --prod
```

### 4.2 Configuração do `vercel.json`

Criar na raiz do projeto:

```json
{
  "buildCommand": "cd frontend-vue && npm install && npm run build",
  "outputDirectory": "frontend-vue/dist",
  "framework": "vue"
}
```

### 4.3 Conexão com o backend

Editar `frontend-vue/src/services/api.ts`, linha 22:

```ts
const API_BASE_URL = "https://fightbase-api.onrender.com/api/v1";
```

Substituir pela URL real do Render caso mude.

### 4.4 Problema comum — CORS

O navegador bloqueia requisições cross-origin com credenciais (JWT) se o backend usar `allow_origins=["*"]`.

**Solução:** Setar `APP_CORS=https://v0-vue-com-python.vercel.app` nas env vars do Render. Atualizar a URL sempre que o frontend mudar.

---

## 5. Configuração do Supabase (Banco de Dados)

### 5.1 Criar o projeto

1. Acessar [supabase.com](https://supabase.com) → New Project
2. Definir nome, senha do banco, região (escolher `us-east-1` pra ficar perto do Render)

### 5.2 Ativar Session Pooler

1. Settings → Database → Connection Pooling
2. Ativar **Session Pooler** (modo Session, porta 5432)

> **Importante:** usar Session Pooler e NÃO Transaction Pooler. O Transaction Pooler derruba conexões a cada transação, quebrando prepared statements do SQLAlchemy.

### 5.3 Obter a string de conexão

Formato:

```
postgresql+asyncpg://postgres.SEU_REF_ID:SUA_SENHA@aws-0-us-east-1.pooler.supabase.co:5432/postgres
```

| Parte                   | Explicação                                     |
| ----------------------- | ---------------------------------------------- |
| `postgresql+asyncpg://` | Protocolo async                                |
| `postgres.SEU_REF_ID`   | Usuário com Ref ID (olhar no painel do pooler) |
| `:SUA_SENHA`            | Senha definida ao criar o projeto              |
| `@aws-0-...`            | Host do pooler (IPv4)                          |
| `:5432`                 | Porta do Session Pooler                        |
| `/postgres`             | Nome do banco                                  |

---

## 6. Problemas Resolvidos

### 6.1 `Network is unreachable` (IPv6 no Render)

**Erro:**

```
sqlalchemy.exc.OperationalError: connection to server at "2600:1f18:..." failed: Network is unreachable
```

**Causa:** Render não suporta IPv6, Supabase resolve direto pra IPv6.

**Solução:** Usar o **Session Pooler** do Supabase que responde em IPv4.

### 6.2 CORS bloqueando requisições

**Erro:**

```
No 'Access-Control-Allow-Origin' header is present on the requested resource
```

**Causa:** Frontend em domínio diferente do backend, com credenciais (JWT).

**Solução:** Setar `APP_CORS` com a URL exata do frontend nas env vars do Render.

---

## 7. Tecnologias do Projeto

### Backend (FastAPI)

| Dependência               | Função                         |
| ------------------------- | ------------------------------ |
| `fastapi`                 | Framework web ASGI             |
| `uvicorn`                 | Servidor ASGI                  |
| `SQLAlchemy` (async)      | ORM                            |
| `asyncpg`                 | Driver PostgreSQL assíncrono   |
| `psycopg`                 | Driver PostgreSQL (migrations) |
| `alembic`                 | Migrations de banco de dados   |
| `scikit-learn` + `pandas` | Modelo de predição ML          |
| `python-jose`             | JWT tokens                     |
| `bcrypt`                  | Hash de senhas                 |

### Frontend (Vue.js)

| Dependência     | Função                  |
| --------------- | ----------------------- |
| `vue` 3         | Framework UI            |
| `vite` 6        | Bundler e dev server    |
| `primevue` 4    | Componentes UI          |
| `tailwindcss` 4 | Estilos                 |
| `pinia` 3       | Gerenciamento de estado |
| `vue-router` 4  | Roteamento              |
| `vue-i18n` 11   | Internacionalização     |

---

## 8. Comandos de Deploy

```powershell
# Deploy do frontend (na pasta raiz fight-base/)
vercel --prod

# Deploy do backend — automático ao fazer push no GitHub
git push origin main

# Backend local (dev)
uvicorn app.main:app --host 0.0.0.0 --port 8080

# Frontend local (dev)
cd frontend-vue && npm run dev
```

---

## 9. Limitações dos Planos Free

| Serviço      | Limitação                                                     |
| ------------ | ------------------------------------------------------------- |
| **Render**   | Backend dorme após 15 min sem tráfego; 1º request demora ~30s |
| **Supabase** | 500 MB storage; 2 projetos free                               |
| **Vercel**   | 100 GB bandwidth/mês                                          |

---

## 10. Como Atualizar

1. Fazer alterações no código local
2. `git add . && git commit -m "..." && git push origin main`
3. **Render** → deploy automático no push
4. **Vercel** → `vercel --prod` (ou ativar auto-deploy no dashboard Vercel)
