# Análise do E-commerce Brasileiro com Python
### Explorando 100 mil pedidos da Olist | 2016–2018

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.2-150458?logo=pandas)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-5.22-3F4F75?logo=plotly)](https://plotly.com/)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.0-FFF000?logo=duckdb)](https://duckdb.org/)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit)](https://streamlit.io/)

---

## Sobre o Projeto

Este projeto surgiu de uma curiosidade: **o que os dados de uma plataforma brasileira de e-commerce revelam sobre comportamento de compra, logística e satisfação dos clientes?**

A partir do dataset público da Olist (disponível no Kaggle), construí um pipeline completo de análise — da limpeza dos dados brutos até a segmentação de clientes com K-Means — usando Python como ferramenta principal.

O objetivo não é só responder perguntas analíticas, mas demonstrar um fluxo de trabalho organizado: código modularizado em `src/`, ETL reproduzível, visualizações padronizadas e análises com storytelling.

---

## Perguntas que Este Projeto Responde

- Quais clientes estão prestes a abandonar a plataforma?
- Quais categorias de produto geram mais receita — e mais satisfação?
- O atraso na entrega realmente derruba a avaliação do vendedor?
- Como segmentar a base de clientes para campanhas de retenção?

---

## Dataset

| | |
|---|---|
| **Fonte** | [Brazilian E-Commerce Public Dataset by Olist — Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) |
| **Licença** | CC BY-NC-SA 4.0 |
| **Volume** | ~100k pedidos, 9 tabelas relacionais |
| **Período** | Set/2016 – Out/2018 |

---

## Estrutura do Projeto

```
olist-ecommerce-analysis/
├── data/
│   ├── raw/                    # CSVs originais do Kaggle (não versionados)
│   └── processed/              # Parquets limpos e enriquecidos
├── notebooks/
│   ├── 01_exploracao_inicial.ipynb
│   ├── 02_limpeza_e_enriquecimento.ipynb
│   ├── 03_analise_receita.ipynb
│   ├── 04_analise_clientes.ipynb
│   ├── 05_segmentacao_rfm.ipynb
│   ├── 06_analise_entregas.ipynb
│   └── 07_analise_vendedores.ipynb
├── src/
│   ├── config.py              # Paths e parâmetros centralizados
│   ├── data_loader.py         # Carregamento e validação dos dados
│   ├── data_cleaner.py        # Limpeza, tipagem e enriquecimento
│   └── visualizations.py      # Funções de visualização reutilizáveis
├── dashboard/
│   └── app.py                 # Dashboard Streamlit interativo
├── reports/
│   └── figures/               # Gráficos exportados
├── tests/
│   └── test_data_cleaner.py   # Testes unitários
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Análises

### 1. Exploração Inicial (`01_exploracao_inicial.ipynb`)
Primeira passagem pelos dados: schema relacional dos 9 datasets, estatísticas descritivas, distribuição de nulos e outliers.

### 2. Limpeza & Enriquecimento (`02_limpeza_e_enriquecimento.ipynb`)
ETL completo — tipagem de datas, tratamento de nulos, feature engineering (dias de entrega, atraso, valor total) e merge de todas as tabelas numa fact table central.

### 3. Análise de Receita (`03_analise_receita.ipynb`)
Evolução mensal do GMV, top categorias, ticket médio por método de pagamento e sazonalidade semanal.

### 4. Análise de Clientes (`04_analise_clientes.ipynb`)
Mapa choropleth por estado, padrão de compra por hora/dia, taxa de recompra e LTV básico.

### 5. Segmentação RFM com K-Means (`05_segmentacao_rfm.ipynb`)
Cálculo de Recência, Frequência e Valor Monetário. Clustering com K=4 (Elbow method), resultando nos segmentos: Champions, Loyalists, At Risk e Lost.

### 6. Análise de Entregas (`06_analise_entregas.ipynb`)
Tempo de entrega por estado, correlação estatística entre atraso e nota de avaliação, e taxa on-time por categoria e região.

### 7. Performance de Vendedores (`07_analise_vendedores.ipynb`)
Score composto (avaliação + pontualidade + volume), top e bottom sellers, e análise de churn de vendedores.

---

## Como Executar

**1. Clone o repositório**
```bash
git clone https://github.com/seu-usuario/olist-ecommerce-analysis.git
cd olist-ecommerce-analysis
```

**2. Crie o ambiente virtual e instale as dependências**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

**3. Baixe os dados**
Acesse o [dataset no Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), baixe e extraia os CSVs para `data/raw/`.

**4. Execute os notebooks na ordem numérica**
```bash
jupyter lab
```

**5. Rode o dashboard (opcional)**
```bash
streamlit run dashboard/app.py
```

---

## Principais Insights

> *(Atualizados conforme as análises são concluídas)*

- **Receita:** ...
- **Entrega:** ...
- **Segmentação RFM:** ...
- **Satisfação:** ...

---

## Tech Stack

| Ferramenta | Papel no Projeto |
|---|---|
| Python 3.11 | Linguagem principal |
| Pandas 2.2 / NumPy | Manipulação e transformação dos dados |
| DuckDB 1.0 | SQL analytics diretamente nos DataFrames |
| Plotly / Seaborn | Visualizações interativas e estáticas |
| Scikit-learn | K-Means para segmentação RFM |
| Streamlit | Dashboard interativo |
| Jupyter Lab | Análise exploratória |

---

## Roadmap

- [x] Estrutura do projeto e configuração
- [x] Módulos `src/` (loader, cleaner, visualizations)
- [x] Notebook 01 — Exploração inicial
- [x] Notebook 02 — Limpeza e ETL
- [ ] Notebook 03 — Análise de receita
- [ ] Notebook 04 — Análise de clientes
- [ ] Notebook 05 — Segmentação RFM
- [ ] Notebook 06 — Análise de entregas
- [ ] Notebook 07 — Performance de vendedores
- [ ] Dashboard Streamlit
- [ ] Testes unitários

---

*Projeto de portfólio — Análise de Dados com Python*
