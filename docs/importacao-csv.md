# Importação de Lutadores do UFC

Este script importa dados reais de lutadores do UFC a partir de um arquivo CSV.

## 📋 Formato do CSV

O arquivo CSV deve ter as seguintes colunas:

```
Fighter_Id,Full Name,Nickname,Ht.,Wt.,Stance,W,L,D,Belt,Round,KD,STR,TD,SUB,Ctrl,Sig. Str. %,Head_%,Body_%,Leg_%,Distance_%,Clinch_%,Ground_%,Sub. Att,Rev.,Weight_Class,Gender,Fighting Style
```

### Colunas Principais:

- **Full Name**: Nome completo do lutador
- **Nickname**: Apelido (opcional)
- **Ht.**: Altura em formato `X.YY` (feet.inches)
- **Wt.**: Peso em libras
- **W, L, D**: Vitórias, Derrotas, Empates
- **KD**: Knockdowns por round (média)
- **STR**: Strikes por round (média)
- **TD**: Takedowns por round (média)
- **Ctrl**: Tempo de controle em segundos (média)
- **Sig. Str. %**: Porcentagem de strikes significativos
- **Sub. Att**: Tentativas de submissão por round
- **Rev.**: Reversões por round
- **Weight_Class**: Categoria de peso
- **Fighting Style**: Striker, Grappler ou Hybrid

## 🎯 Como o Script Calcula os Atributos

O script converte estatísticas reais do UFC em atributos de 0-100:

### 1. **Striking (0-100)**

- Volume de strikes por round
- Precisão (Sig. Str. %)
- Poder de nocaute (KD)

### 2. **Grappling (0-100)**

- Takedowns por round
- Tempo de controle
- Porcentagem de luta no chão

### 3. **Defense (0-100)**

- Reversões
- Cartel (vitórias vs derrotas)
- Base média de 50

### 4. **Stamina (0-100)**

- Média de rounds lutados
- Sustentação de controle
- Volume constante de atividade

### 5. **Speed (0-100)**

- Volume de strikes
- Luta à distância (Distance %)
- Knockdowns (indica velocidade)

### 6. **Strategy (0-100)**

- Diversidade de técnicas (clinch, ground, distance)
- Tentativas de submissão
- Win rate

## 🚀 Como Usar

### 1. Prepare o CSV

Salve seu arquivo CSV em algum lugar acessível, por exemplo:

```bash
/home/udson-rego/Documentos/estudos/fight-base/fight-base/data/ufc_fighters.csv
```

### 2. Execute o Script

```bash
# Certifique-se de estar no diretório do projeto
cd /home/udson-rego/Documentos/estudos/fight-base/fight-base

# Execute o script
python scripts/import_fighters_from_csv.py data/ufc_fighters.csv
```

### 3. Verifique a Importação

O script irá:

1. Ler o CSV
2. Calcular atributos baseados nas estatísticas
3. Salvar no banco de dados
4. Mostrar exemplos dos lutadores importados

Exemplo de saída:

```
📂 Lendo arquivo: data/ufc_fighters.csv
✅ 500 lutadores lidos do CSV
💾 Salvando no banco de dados...
✅ 500 lutadores importados com sucesso!

📊 Exemplos de lutadores importados:
  - Danny Abbadi (The Assassin)
    Cartel: 4-6-0
    Overall: 65.3
    Striking: 72, Grappling: 58
  - David Abbott (Tank)
    Cartel: 10-15-0
    Overall: 68.5
    Striking: 75, Grappling: 62
```

## 📊 Exemplo de Dados Importados

Para o lutador **Danny Abbadi**:

**Estatísticas CSV:**

- W: 4, L: 6, D: 0
- STR: 29.5 strikes/round
- Sig. Str. %: 36%
- KD: 0.0
- TD: 0.0
- Ctrl: 55 segundos

**Atributos Calculados:**

- Striking: 72 (bom volume, precisão ok)
- Grappling: 58 (sem takedowns, controle moderado)
- Defense: 50 (base, sem reversões)
- Stamina: 65 (2 rounds médios)
- Speed: 68 (volume razoável)
- Strategy: 62 (híbrido)

## ⚙️ Customizações

### Ajustar Cálculos

Edite as funções em `import_fighters_from_csv.py`:

- `calculate_attributes()`: Altera como atributos são calculados
- `parse_height()`: Muda conversão de altura
- `parse_weight()`: Muda conversão de peso

### Adicionar Mais Dados

O script cria um campo `cartel` (lista vazia por padrão). Se você tiver dados de lutas individuais, pode popular:

```python
cartel = [
    {
        "opponent": "John Doe",
        "result": "W",
        "method": "KO",
        "round": 2,
        "date": "2024-01-15",
        "organization": "UFC"
    }
]
```

## 🔍 Validação

Após importar, você pode validar via API:

```bash
# Listar lutadores
curl http://localhost:8000/api/v1/fighters

# Buscar por nome
curl http://localhost:8000/api/v1/fighters/search?name=Danny

# Ver top fighters
curl http://localhost:8000/api/v1/fighters/top?limit=10
```

## ⚠️ Observações

1. **ID do Criador**: O script usa um UUID temporário. Idealmente deveria usar um usuário admin real.

2. **Atributos Mínimos**: Todos os atributos têm mínimo de 30 para garantir lutadores funcionais.

3. **Estimativas**: KO_wins e Submission_wins são estimados se não vierem no CSV.

4. **Cartel vs Wins/Losses**:
   - `wins`, `losses`, `draws` são os campos antigos (ainda presentes para compatibilidade)
   - `cartel` é o novo campo (lista de lutas detalhadas)

## 🐛 Troubleshooting

**Erro: "Arquivo não encontrado"**

- Verifique o caminho do CSV
- Use caminho absoluto se necessário

**Erro: "Database connection failed"**

- Certifique-se que o PostgreSQL está rodando
- Verifique as variáveis de ambiente em `.env`

**Lutadores com atributos baixos**

- Normal para lutadores com poucos dados
- Mínimo de 30 é garantido para todos os atributos

**Dados faltando**

- O script lida com valores vazios/nan
- Usa defaults seguros quando dados estão ausentes
