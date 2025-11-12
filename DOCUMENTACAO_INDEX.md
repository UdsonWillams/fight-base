# 📚 FightBase - Índice de Documentação

## 🚀 Início Rápido

### Para Usuários

1. **[QUICKSTART.md](QUICKSTART.md)** ⭐ **COMECE AQUI!**

   - Setup em 5 minutos
   - Primeiros passos no Swagger
   - Criar primeiro lutador
   - Simular primeira luta

2. **[README.md](README.md)** - Visão Geral Completa
   - O que é o FightBase
   - Principais recursos
   - Instalação e configuração
   - Exemplos básicos de uso
   - Tecnologias utilizadas

## 📖 Documentação de Uso

### Guias Práticos

3. **[docs/EXEMPLOS_PRATICOS.md](docs/EXEMPLOS_PRATICOS.md)** - Exemplos Completos

   - Todos os endpoints com curl
   - Autenticação passo a passo
   - CRUD de lutadores
   - Simulações e análises
   - Cenários completos de uso
   - Troubleshooting

4. **[docs/CASOS_DE_USO.md](docs/CASOS_DE_USO.md)** - Casos de Uso e Ideias
   - Casos de uso atuais
   - Rankings e comparações
   - Perguntas "E se..."
   - Ideias para expansão futura
   - Roadmap técnico
   - Público-alvo

## 🔧 Documentação Técnica

### Para Desenvolvedores

5. **[docs/ALGORITMO_TECNICO.md](docs/ALGORITMO_TECNICO.md)** - Algoritmo Detalhado

   - Como funciona a simulação
   - Cálculos de poder
   - Probabilidades
   - Tipos de resultado
   - Validações
   - Melhorias futuras com ML

6. **[REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)** - Resumo da Refatoração

   - Componentes criados
   - Modelos de dados
   - Schemas e repositórios
   - Serviços e endpoints
   - Arquitetura aplicada
   - Estatísticas do projeto

7. **[PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md)** - Roadmap e Próximos Passos
   - Tarefas imediatas
   - Curto, médio e longo prazo
   - Features sugeridas
   - Checklist de qualidade
   - Metas de negócio

## 📊 Visão Geral da Arquitetura

```
FightBase
│
├── 🥋 Lutadores (Fighters)
│   ├── Modelo: 6 atributos (0-100)
│   ├── CRUD completo
│   ├── Busca avançada
│   └── Rankings
│
├── ⚔️ Simulações (Fight Simulations)
│   ├── Algoritmo inteligente
│   ├── Round a round
│   ├── Probabilidades calculadas
│   └── Tipos de resultado (KO/Sub/Dec)
│
├── 📊 Análises
│   ├── Comparação de lutadores
│   ├── Previsão de resultados
│   ├── Histórico de confrontos
│   └── Estatísticas agregadas
│
└── 🔐 Autenticação
    ├── JWT tokens
    ├── Roles (admin/user)
    └── Controle de acesso
```

## 🎯 Guias por Objetivo

### "Quero começar a usar AGORA!"

1. [QUICKSTART.md](QUICKSTART.md)
2. [README.md](README.md) - Seção "Exemplos de Uso"

### "Quero entender como funciona"

1. [README.md](README.md) - Seção "Como Funciona a Simulação"
2. [docs/ALGORITMO_TECNICO.md](docs/ALGORITMO_TECNICO.md)

### "Quero ver exemplos práticos"

1. [docs/EXEMPLOS_PRATICOS.md](docs/EXEMPLOS_PRATICOS.md)
2. Swagger UI: http://localhost:8000/swagger

### "Quero contribuir/desenvolver"

1. [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)
2. [PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md)
3. [docs/ALGORITMO_TECNICO.md](docs/ALGORITMO_TECNICO.md)

### "Quero ideias de features"

1. [docs/CASOS_DE_USO.md](docs/CASOS_DE_USO.md)
2. [PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md)

## 📁 Estrutura de Arquivos

### Raiz do Projeto

```
fight-base/
├── README.md                    ⭐ Visão geral
├── QUICKSTART.md               ⚡ Início rápido (5 min)
├── REFACTORING_SUMMARY.md      📋 Resumo completo
├── PROXIMOS_PASSOS.md          🚀 Roadmap
├── COMMIT_MESSAGE.md           📝 Mensagem de commit
│
├── docs/                       📚 Documentação detalhada
│   ├── EXEMPLOS_PRATICOS.md   🎯 Exemplos com curl
│   ├── CASOS_DE_USO.md        💡 Casos de uso e ideias
│   ├── ALGORITMO_TECNICO.md   🧠 Detalhes do algoritmo
│   └── alembic.md             🔧 Migrações
│
├── app/                        💻 Código da aplicação
│   ├── api/v1/                🌐 Endpoints REST
│   │   ├── fighters/          🥋 Lutadores
│   │   └── simulations/       ⚔️ Simulações
│   ├── database/              🗄️ Modelos e repositórios
│   ├── schemas/               📝 Schemas Pydantic
│   ├── services/              🎯 Lógica de negócio
│   └── core/                  ⚙️ Configurações
│
├── migrations/                 📊 Migrações do banco
├── tests/                      🧪 Testes
└── scripts/                    🔧 Scripts úteis
```

## 🔗 Links Rápidos

### Documentação Interativa

- [Swagger UI](http://localhost:8000/swagger) - Testar endpoints
- [ReDoc](http://localhost:8000/docs) - Documentação bonita
- [OpenAPI JSON](http://localhost:8000/openapi.json) - Spec da API

### Código no GitHub

- [Repositório](https://github.com/UdsonWillams/fight-base)
- [Issues](https://github.com/UdsonWillams/fight-base/issues)
- [Pull Requests](https://github.com/UdsonWillams/fight-base/pulls)

## 📖 Ordem de Leitura Recomendada

### Para Entender o Projeto (30 min)

1. README.md (10 min)
2. QUICKSTART.md (5 min)
3. docs/EXEMPLOS_PRATICOS.md (15 min)

### Para Usar Profissionalmente (1h)

1. README.md (10 min)
2. QUICKSTART.md (5 min)
3. docs/EXEMPLOS_PRATICOS.md (20 min)
4. docs/ALGORITMO_TECNICO.md (15 min)
5. Swagger UI - Testar (10 min)

### Para Desenvolver/Contribuir (2h)

1. README.md (10 min)
2. REFACTORING_SUMMARY.md (30 min)
3. docs/ALGORITMO_TECNICO.md (20 min)
4. Código-fonte - Explorar (40 min)
5. PROXIMOS_PASSOS.md (20 min)

## 🎓 Por Nível de Experiência

### Iniciante

✅ README.md
✅ QUICKSTART.md
✅ Swagger UI (testar na interface)

### Intermediário

✅ docs/EXEMPLOS_PRATICOS.md
✅ docs/CASOS_DE_USO.md
✅ Código da API (endpoints)

### Avançado

✅ docs/ALGORITMO_TECNICO.md
✅ REFACTORING_SUMMARY.md
✅ Código dos serviços e repositórios
✅ PROXIMOS_PASSOS.md

## 🔍 Buscar por Tópico

### Autenticação

- README.md - Seção "Autenticação"
- docs/EXEMPLOS_PRATICOS.md - Seção "Autenticação"

### Lutadores

- README.md - Seção "Gerenciamento de Lutadores"
- docs/EXEMPLOS_PRATICOS.md - Seção "Gerenciamento de Lutadores"
- app/api/v1/fighters/views.py

### Simulações

- README.md - Seção "Simulação de Lutas"
- docs/EXEMPLOS_PRATICOS.md - Seção "Simulação de Lutas"
- docs/ALGORITMO_TECNICO.md (completo)
- app/services/domain/fight_simulation.py

### Algoritmo

- README.md - Seção "Como Funciona a Simulação"
- docs/ALGORITMO_TECNICO.md (detalhado)

### Deploy

- README.md - Seções "Configuração" e "Executando"
- QUICKSTART.md

### Testes

- PROXIMOS_PASSOS.md - Seção "Testes"
- tests/ (código)

### Contribuir

- PROXIMOS_PASSOS.md
- docs/CASOS_DE_USO.md - Seção "Contribuindo"
- REFACTORING_SUMMARY.md

## ❓ FAQ Rápido

**Q: Como começar?**
A: [QUICKSTART.md](QUICKSTART.md)

**Q: Como usar a API?**
A: [docs/EXEMPLOS_PRATICOS.md](docs/EXEMPLOS_PRATICOS.md)

**Q: Como funciona o algoritmo?**
A: [docs/ALGORITMO_TECNICO.md](docs/ALGORITMO_TECNICO.md)

**Q: Quais são as próximas features?**
A: [PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md)

**Q: Como foi feita a refatoração?**
A: [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)

**Q: Tem exemplos de uso?**
A: [docs/EXEMPLOS_PRATICOS.md](docs/EXEMPLOS_PRATICOS.md)

**Q: Para que serve?**
A: [README.md](README.md) e [docs/CASOS_DE_USO.md](docs/CASOS_DE_USO.md)

## 📞 Suporte

### Encontrou um problema?

1. Verifique [docs/EXEMPLOS_PRATICOS.md](docs/EXEMPLOS_PRATICOS.md) - Seção "Troubleshooting"
2. Abra uma [Issue no GitHub](https://github.com/UdsonWillams/fight-base/issues)

### Tem uma ideia?

1. Veja [docs/CASOS_DE_USO.md](docs/CASOS_DE_USO.md) - Talvez já esteja lá!
2. Abra uma Issue com label "enhancement"

### Quer contribuir?

1. Leia [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)
2. Veja [PROXIMOS_PASSOS.md](PROXIMOS_PASSOS.md)
3. Fork e PR!

## 🎉 Comece Agora!

Escolha seu caminho:

### 🚀 Quero usar rapidamente

→ [QUICKSTART.md](QUICKSTART.md)

### 📚 Quero entender tudo

→ [README.md](README.md)

### 💻 Quero desenvolver

→ [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md)

### 🎯 Quero exemplos práticos

→ [docs/EXEMPLOS_PRATICOS.md](docs/EXEMPLOS_PRATICOS.md)

---

**Boa luta! 🥊**
