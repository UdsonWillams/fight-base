# 🥊 FightBase - MMA Fighter Database & Simulation API

> Banco de dados de lutadores com sistema inteligente de simulação de lutas baseado em estatísticas

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-00a393?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ed?logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-pytest-0a9edc?logo=pytest&logoColor=white)](https://pytest.org/)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-000000?logo=python&logoColor=white)](https://docs.astral.sh/ruff/)

FightBase é uma API REST que permite cadastrar lutadores de MMA (reais ou fictícios), comparar estatísticas e simular lutas baseadas em atributos realistas como striking, grappling, defesa, resistência, velocidade e estratégia.

## 🎯 Principais Recursos

### 🥋 Gestão de Lutadores

- ✅ **Cadastro completo** de lutadores com atributos detalhados (0-100)
- 🏆 **Organizações**: UFC, Bellator, ONE Championship, PFL, etc
- ⚖️ **Categorias de peso** e estilos de luta
- 📊 **Estatísticas reais**: cartel, vitórias por KO/finalização
- 🎭 **Lutadores fictícios**: crie seus próprios lutadores personalizados
- � **Perfis detalhados**: bio, idade, altura, envergadura

### 🎮 Sistema de Simulação

- ⚔️ **Simulação completa** de lutas round a round
- 🎲 **Algoritmo inteligente** que considera:
  - Striking vs Striking
  - Grappling vs Grappling
  - Defesa, resistência, velocidade e QI de luta
  - Histórico real (cartel)
  - Aleatoriedade realista
- 📈 **Probabilidades calculadas** antes da luta
- 🏁 **Tipos de resultado**: KO, Finalização ou Decisão
- 📜 **Detalhes round a round** com eventos importantes

### 📊 Comparação e Análise

- 🆚 **Compare dois lutadores** lado a lado
- 🔍 **Análise de vantagens** em cada atributo
- � **Previsão de resultados** sem executar simulação
- 🏆 **Rankings** por organização e categoria
- 📈 **Estatísticas agregadas** do sistema

### 🔐 Autenticação e Controle

- 🔐 **Autenticação JWT** com roles (admin/user)
- 👤 **Sistema de usuários** - cada um cria seus lutadores
- �️ **Autorização baseada em roles**
- 📚 **Documentação automática** com Swagger

## Requisitos

- Python 3.12
- Docker & Docker Compose
- **PostgreSQL** (necessário para executar testes localmente)

## Configuração Inicial

1. Clone o repositório:

   ```sh
   git clone https://github.com/udsonwillams/challenge
   cd challenge
   ```

2. Crie o arquivo `.env` com base no `.env.example`:

   ```sh
   cp .env.example .env
   ```

3. Configure as variáveis de ambiente necessárias no `.env`:
   ```env
   SECRET_KEY=sua-chave-secreta-aqui
   POSTGRES_USER=myuser
   POSTGRES_PASSWORD=mypassword
   POSTGRES_DB=challenger_db
   EXTERNAL_PRODUCTS_BASE_URL=https://serverest.dev
   ADMIN_DEFAULT_EMAIL=admin@mail.com
   ADMIN_DEFAULT_PASSWORD=pass@word
   ```

## Executando a Aplicação

### Com Docker (Recomendado)

1. Construa e inicie os contêineres:

   ```sh
   docker-compose up --build
   ```

2. Acesse a aplicação em `http://localhost:8000`

### Localmente (Desenvolvimento)

1. **Instale o PostgreSQL (obrigatório para testes):**

   **Ubuntu/Debian:**

   ```sh
   sudo apt update
   sudo apt install postgresql postgresql-contrib postgresql-client
   ```

   **macOS (com Homebrew):**

   ```sh
   brew install postgresql
   ```

   **Windows:**

   - Baixe e instale do [site oficial do PostgreSQL](https://www.postgresql.org/download/windows/)

2. **Verificar instalação do PostgreSQL:**

   ```sh
   pg_ctl --version
   # Deve retornar a versão instalada
   ```

3. Crie e ative o ambiente virtual:

   ```sh
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou
   venv\Scripts\activate     # Windows
   ```

4. Instale as dependências:

   ```sh
   pip install -r requirements-dev.txt
   ```

5. Execute as migrações do banco:

   ```sh
   alembic upgrade head
   ```

6. Inicie o servidor:
   ```sh
   uvicorn app.main:app --reload
   # ou
   make runserver
   ```

## Usuário Administrador Padrão

Para criar o usuário administrador inicial, execute:

```sh
python scripts/create_admin.py
```

Credenciais padrão:

- **Email**: admin@mail.com
- **Senha**: pass@word

## 📖 Exemplos de Uso da API

### 🔐 Autenticação

```sh
# Login e obter token JWT
POST /api/v1/auth/token
{
  "email": "admin@mail.com",
  "password": "pass@word"
}
```

### 🥋 Gerenciamento de Lutadores

```sh
# Criar novo lutador
POST /api/v1/fighters
Authorization: Bearer <token>
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
  "ko_wins": 10,
  "submission_wins": 6,
  "age": 36,
  "height_cm": 193,
  "reach_cm": 215,
  "bio": "Ex-campeão dos meio-pesados, considerado um dos maiores de todos os tempos",
  "is_real": true
}

# Buscar lutadores com filtros
GET /api/v1/fighters?organization=UFC&weight_class=Peso-pesado&limit=10

# Ver top lutadores
GET /api/v1/fighters/rankings/top?limit=10&organization=UFC

# Buscar lutador por ID
GET /api/v1/fighters/{fighter_id}

# Atualizar lutador
PUT /api/v1/fighters/{fighter_id}
Authorization: Bearer <token>
{
  "wins": 28,
  "striking": 93
}

# Ver meus lutadores criados
GET /api/v1/fighters/my/fighters
Authorization: Bearer <token>

# Estatísticas gerais
GET /api/v1/fighters/statistics/overview
```

### ⚔️ Simulação de Lutas

```sh
# Simular uma luta completa
POST /api/v1/simulations
Authorization: Bearer <token>
{
  "fighter1_id": "uuid-do-jon-jones",
  "fighter2_id": "uuid-do-stipe-miocic",
  "rounds": 5,
  "notes": "Luta pelo título dos pesados"
}

# Resposta incluirá:
# - Vencedor e tipo de vitória (KO/Submission/Decision)
# - Probabilidades calculadas
# - Detalhes round a round
# - Eventos importantes de cada round

# Prever resultado sem simular
GET /api/v1/simulations/predict?fighter1_id={id1}&fighter2_id={id2}

# Resposta incluirá:
# - Probabilidades de vitória de cada lutador
# - Probabilidade de KO, Finalização ou Decisão
# - Análise de vantagens (striking, grappling, etc)
# - Fatores-chave da luta

# Comparar dois lutadores
GET /api/v1/simulations/compare?fighter1_id={id1}&fighter2_id={id2}

# Ver histórico de simulações de um lutador
GET /api/v1/simulations/history/{fighter_id}?limit=20

# Ver confrontos diretos entre dois lutadores
GET /api/v1/simulations/matchup?fighter1_id={id1}&fighter2_id={id2}

# Ver simulações recentes do sistema
GET /api/v1/simulations/recent?limit=50
```

### 🎯 Exemplo de Fluxo Completo

```sh
# 1. Criar conta e fazer login
POST /api/v1/customers
{
  "email": "fan@mma.com",
  "password": "senha123",
  "name": "MMA Fan"
}

POST /api/v1/auth/token
{
  "email": "fan@mma.com",
  "password": "senha123"
}

# 2. Criar dois lutadores
POST /api/v1/fighters
Authorization: Bearer <token>
{
  "name": "Khabib Nurmagomedov",
  "organization": "UFC",
  "weight_class": "Peso-leve",
  "fighting_style": "Grappler",
  "striking": 78,
  "grappling": 98,
  "defense": 92,
  "stamina": 95,
  "speed": 82,
  "strategy": 96,
  ...
}

POST /api/v1/fighters
{
  "name": "Conor McGregor",
  "organization": "UFC",
  "weight_class": "Peso-leve",
  "fighting_style": "Striker",
  "striking": 96,
  "grappling": 72,
  "defense": 75,
  "stamina": 80,
  "speed": 90,
  "strategy": 85,
  ...
}

# 3. Comparar os lutadores
GET /api/v1/simulations/compare?fighter1_id={khabib_id}&fighter2_id={mcgregor_id}

# 4. Ver previsão
GET /api/v1/simulations/predict?fighter1_id={khabib_id}&fighter2_id={mcgregor_id}

# 5. Simular a luta
POST /api/v1/simulations
{
  "fighter1_id": "{khabib_id}",
  "fighter2_id": "{mcgregor_id}",
  "rounds": 5
}
```

## Documentação da API

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Testes

**⚠️ IMPORTANTE:** Para executar testes, instale o PostgreSQL:

```sh
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql-all

# Ou apenas o necessário:
sudo apt install postgresql postgresql-client-common postgresql-common

# Verificar se funcionou:
pg_ctl --version
```

### Executar todos os testes:

```sh
make coverage
```

### Executar com cobertura:

```sh
make coverage
# ou
pytest --cov=app --cov-report=html
```

### Executar testes específicos:

```sh
# Testes de integração
pytest tests/integration/

# Testes de clientes
pytest tests/integration/api/v1/customers/

# Teste específico
pytest tests/integration/api/v1/customers/test_customer.py::test_create_and_get_customer
```

## 📂 Estrutura do Projeto

```
app/
├── api/v1/                    # Endpoints da API
│   ├── auth/                 # Rotas de autenticação
│   ├── fighters/             # 🥋 Rotas de lutadores (CRUD)
│   ├── simulations/          # ⚔️ Rotas de simulação de lutas
│   ├── customers/            # Rotas de usuários (legado)
│   └── products/             # Rotas de produtos (legado)
├── core/                      # Configurações centrais
│   ├── settings.py           # Configurações da aplicação
│   └── logger.py             # Sistema de logs
├── database/                  # Modelos e repositórios
│   ├── models/
│   │   ├── base.py           # 🥊 Modelos: Fighter, FightSimulation, User
│   │   └── schemas.py        # Schemas Pydantic dos modelos
│   └── repositories/
│       ├── fighter.py        # 🥋 Repositório de lutadores
│       ├── fight_simulation.py # ⚔️ Repositório de simulações
│       └── base.py           # Repositório base
├── schemas/                   # Schemas Pydantic
│   ├── auth.py               # Schemas de autenticação
│   └── domain/
│       ├── fighters/         # 🥋 Schemas de lutadores
│       │   ├── input.py      # Schemas de entrada (Create/Update)
│       │   └── output.py     # Schemas de saída (Response)
│       └── simulations.py    # ⚔️ Schemas de simulações
├── services/                  # Lógica de negócio
│   ├── auth/                 # Serviços de autenticação
│   └── domain/
│       ├── fighter.py        # 🥋 Serviço de lutadores
│       └── fight_simulation.py # ⚔️ Serviço de simulação (algoritmo)
├── middlewares/              # Middlewares
└── exceptions/               # Exceções customizadas
```

## 🧠 Como Funciona a Simulação

O algoritmo de simulação considera múltiplos fatores:

### 1. **Cálculo de Poder**

- **Striking Power**: `striking × 0.5 + speed × 0.3 + defense × 0.2`
- **Grappling Power**: `grappling × 0.5 + stamina × 0.3 + strategy × 0.2`
- **Overall Power**: Média de todos os atributos

### 2. **Probabilidades de Vitória**

- Baseado no poder geral de cada lutador
- Ajustado pelo histórico (cartel real)
- Normalizado para somar 100%

### 3. **Tipo de Resultado**

- **KO**: Influenciado pela diferença de striking
- **Finalização**: Influenciado pela diferença de grappling
- **Decisão**: Quando os lutadores são equilibrados

### 4. **Simulação Round a Round**

- Cada round calcula pontos para ambos lutadores
- Aleatoriedade de 10-30% para realismo
- Eventos especiais: takedowns, golpes significativos, tentativas de finalização
- Determina dominância e gera narrativa

### 5. **Resultado Final**

- Soma dos pontos de todos os rounds
- Aplicação do tipo de resultado (KO/Submission/Decision)
- Geração de detalhes completos da luta

## 🎯 Atributos dos Lutadores (0-100)

| Atributo      | Descrição                        | Importância             |
| ------------- | -------------------------------- | ----------------------- |
| **Striking**  | Habilidade de trocação em pé     | Alta no stand-up        |
| **Grappling** | Habilidade de luta agarrada/chão | Alta em finalizações    |
| **Defense**   | Capacidade defensiva geral       | Reduz dano recebido     |
| **Stamina**   | Resistência/Cardio               | Crucial em lutas longas |
| **Speed**     | Velocidade de movimento e golpes | Vantagem tática         |
| **Strategy**  | QI de luta/Game plan             | Decisões inteligentes   |

**Overall Rating**: Média dos 6 atributos (calculado automaticamente)

## Tecnologias Utilizadas

- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para Python
- **PostgreSQL** - Banco de dados relacional
- **JWT** - Autenticação via tokens
- **Pydantic** - Validação de dados
- **pytest** - Framework de testes
- **Docker** - Containerização
- **Alembic** - Migrações de banco

## Ferramentas de Desenvolvimento

- **Ruff** - Linting e formatação
- **pre-commit** - Hooks de commit
- **ipdb** - Debugging
- **pytest-cov** - Cobertura de testes

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
