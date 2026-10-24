"""Dashboard interativo da análise do e-commerce Olist.

Execute a partir da raiz do projeto:
    streamlit run dashboard/app.py

Requer os arquivos gerados pelos notebooks 02, 05, 06 e 07 em data/processed/.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import COLORS, PROCESSED_FILES
from src.visualizations import format_brl

st.set_page_config(page_title="Olist — Análise de E-commerce", page_icon="📦", layout="wide")

ORDEM_SEGMENTOS = ["Recorrentes", "Recentes de alto valor", "Recentes de baixo valor", "Inativos"]
CORES_SEGMENTOS = dict(zip(ORDEM_SEGMENTOS, [COLORS["secondary"], COLORS["primary"], "#44BBA4", "#9E9E9E"]))
FAIXAS_ATRASO = [-np.inf, -15, -8, -1, 0, 3, 7, 14, np.inf]
ROTULOS_ATRASO = ["15+ dias antes", "8–14 antes", "1–7 antes", "No dia",
                  "1–3 atraso", "4–7 atraso", "8–14 atraso", "15+ atraso"]


# ── Dados ─────────────────────────────────────────────────────────────────────

@st.cache_data
def carregar_dados():
    faltando = [p.name for p in PROCESSED_FILES.values() if not p.exists()]
    if faltando:
        return None, faltando
    pedidos = pd.read_parquet(PROCESSED_FILES["orders_enriched"])
    pedidos = pedidos[pedidos["is_delivered"] & pedidos["revenue"].notna()].copy()
    pedidos["mes"] = pedidos["order_purchase_timestamp"].dt.to_period("M").dt.to_timestamp()
    rfm = pd.read_parquet(PROCESSED_FILES["rfm"])
    vendedores = pd.read_parquet(PROCESSED_FILES["seller_performance"])
    return {"pedidos": pedidos, "rfm": rfm, "vendedores": vendedores}, []


dados, faltando = carregar_dados()

st.title("Análise do E-commerce Brasileiro — Olist")
st.caption("96 mil pedidos entregues entre 2016 e 2018 · dataset público da Olist (Kaggle, CC BY-NC-SA 4.0)")

if dados is None:
    st.error(
        "Arquivos processados não encontrados: " + ", ".join(faltando) + ".\n\n"
        "Baixe os CSVs do Kaggle para `data/raw/` e execute os notebooks 02, 05, 06 e 07 antes de abrir o dashboard."
    )
    st.stop()

pedidos_todos = dados["pedidos"]

# ── Filtros ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Filtros")
    meses = sorted(pedidos_todos["mes"].unique())
    inicio, fim = st.select_slider(
        "Período (mês da compra)",
        options=meses,
        value=(pd.Timestamp("2017-01-01"), meses[-1]),
        format_func=lambda m: pd.Timestamp(m).strftime("%m/%Y"),
    )
    estados = sorted(pedidos_todos["customer_state"].dropna().unique())
    estados_sel = st.multiselect("Estados do cliente", estados, placeholder="Todos")
    st.caption("Os filtros valem para as abas Visão geral e Entregas. "
               "Segmentos e vendedores usam o período completo, como nos notebooks.")

pedidos = pedidos_todos[pedidos_todos["mes"].between(inicio, fim)]
if estados_sel:
    pedidos = pedidos[pedidos["customer_state"].isin(estados_sel)]

if pedidos.empty:
    st.warning("Nenhum pedido para os filtros escolhidos.")
    st.stop()

aba_geral, aba_clientes, aba_entregas, aba_vendedores = st.tabs(
    ["Visão geral", "Clientes (RFM)", "Entregas", "Vendedores"]
)

# ── Visão geral ───────────────────────────────────────────────────────────────

with aba_geral:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Receita (sem frete)", format_brl(pedidos["revenue"].sum()))
    c2.metric("Pedidos", f"{len(pedidos):,}".replace(",", "."))
    c3.metric("Ticket médio", format_brl(pedidos["revenue"].mean()))
    c4.metric("Nota média", f"{pedidos['review_score'].mean():.2f}".replace(".", ","))
    c5.metric("Entregues no prazo", f"{pedidos['delivered_on_time'].mean():.1%}".replace(".", ","))

    mensal = pedidos.groupby("mes").agg(receita=("revenue", "sum"), pedidos=("order_id", "count")).reset_index()
    fig = px.area(mensal, x="mes", y="receita", title="Receita mensal",
                  labels={"mes": "", "receita": "Receita (R$)"}, color_discrete_sequence=[COLORS["primary"]])
    fig.update_layout(plot_bgcolor="white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    categorias = (
        pedidos.groupby("main_category")["revenue"].sum()
        .nlargest(10).sort_values().reset_index()
    )
    fig = px.bar(categorias, x="revenue", y="main_category", orientation="h", title="Top 10 categorias por receita",
                 labels={"revenue": "Receita (R$)", "main_category": ""}, color_discrete_sequence=[COLORS["primary"]])
    fig.update_layout(plot_bgcolor="white")
    col_a.plotly_chart(fig, use_container_width=True)

    pagamentos = pedidos["payment_type"].value_counts().reset_index()
    pagamentos.columns = ["metodo", "pedidos"]
    fig = px.pie(pagamentos, names="metodo", values="pedidos", title="Pedidos por método de pagamento",
                 color_discrete_sequence=COLORS["palette"], hole=0.45)
    col_b.plotly_chart(fig, use_container_width=True)

# ── Clientes (RFM) ────────────────────────────────────────────────────────────

with aba_clientes:
    rfm = dados["rfm"]
    perfil = (
        rfm.groupby("segment")
        .agg(clientes=("customer_unique_id", "count"), recencia=("recency", "mean"),
             frequencia=("frequency", "mean"), valor=("monetary", "mean"), receita=("monetary", "sum"))
        .reindex(ORDEM_SEGMENTOS)
    )
    perfil["% clientes"] = perfil["clientes"] / perfil["clientes"].sum() * 100
    perfil["% receita"] = perfil["receita"] / perfil["receita"].sum() * 100

    st.markdown(
        "Segmentação com K-Means (k=4) sobre Recência, Frequência e Valor de cada cliente. "
        "Detalhes e escolha do k no notebook `05_segmentacao_rfm`."
    )
    colunas = st.columns(4)
    for col, seg in zip(colunas, ORDEM_SEGMENTOS):
        linha = perfil.loc[seg]
        col.metric(seg, f"{linha['clientes']:,.0f}".replace(",", "."),
                   f"{linha['% receita']:.1f}% da receita".replace(".", ","), delta_color="off")

    col_a, col_b = st.columns(2)
    comparacao = perfil[["% clientes", "% receita"]].reset_index().melt(id_vars="segment", var_name="medida", value_name="pct")
    fig = px.bar(comparacao, x="segment", y="pct", color="medida", barmode="group",
                 title="Peso de cada segmento", labels={"segment": "", "pct": "%", "medida": ""},
                 color_discrete_sequence=[COLORS["primary"], COLORS["accent"]])
    fig.update_layout(plot_bgcolor="white")
    col_a.plotly_chart(fig, use_container_width=True)

    amostra = rfm.sample(5000, random_state=42)
    fig = px.scatter(amostra, x="recency", y="monetary", color="segment", log_y=True, opacity=0.5,
                     category_orders={"segment": ORDEM_SEGMENTOS}, color_discrete_map=CORES_SEGMENTOS,
                     title="Recência × valor (amostra de 5 mil clientes)",
                     labels={"recency": "Recência (dias)", "monetary": "Valor gasto (R$)", "segment": ""})
    fig.update_layout(plot_bgcolor="white")
    col_b.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        perfil.drop(columns="receita").style.format({
            "clientes": "{:,.0f}", "recencia": "{:.0f} dias", "frequencia": "{:.2f}",
            "valor": "R$ {:,.2f}", "% clientes": "{:.1f}%", "% receita": "{:.1f}%",
        }),
        use_container_width=True,
    )

# ── Entregas ──────────────────────────────────────────────────────────────────

with aba_entregas:
    entregas = pedidos[pedidos["delivery_days"].notna()].copy()
    atrasados = entregas["delivery_delay_days"] > 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Prazo real (mediana)", f"{entregas['delivery_days'].median():.0f} dias")
    c2.metric("Prazo prometido (mediana)", f"{entregas['days_to_estimated'].median():.0f} dias")
    c3.metric("Nota — no prazo", f"{entregas.loc[~atrasados, 'review_score'].mean():.2f}".replace(".", ","))
    c4.metric("Nota — atrasado", f"{entregas.loc[atrasados, 'review_score'].mean():.2f}".replace(".", ","))

    col_a, col_b = st.columns(2)
    entregas["faixa_atraso"] = pd.cut(entregas["delivery_delay_days"], bins=FAIXAS_ATRASO, labels=ROTULOS_ATRASO)
    por_faixa = entregas.groupby("faixa_atraso", observed=True)["review_score"].agg(["mean", "count"]).reset_index()
    por_faixa["tipo"] = np.where(por_faixa["faixa_atraso"].astype(str).str.contains("atraso"), "Atrasado", "No prazo")
    fig = px.bar(por_faixa, x="faixa_atraso", y="mean", color="tipo", title="Nota média por faixa de atraso",
                 labels={"faixa_atraso": "", "mean": "Nota média", "tipo": "", "count": "Pedidos"},
                 hover_data={"count": True}, color_discrete_map={"No prazo": COLORS["primary"], "Atrasado": COLORS["success"]})
    fig.update_layout(plot_bgcolor="white", yaxis_range=[0, 5])
    col_a.plotly_chart(fig, use_container_width=True)

    por_estado = (
        entregas.groupby("customer_state")
        .agg(pedidos=("order_id", "count"), no_prazo=("delivered_on_time", "mean"), prazo=("delivery_days", "median"))
        .reset_index()
    )
    por_estado["no_prazo"] *= 100
    por_estado = por_estado.sort_values("no_prazo")
    fig = px.bar(por_estado, x="no_prazo", y="customer_state", orientation="h",
                 title="% entregue no prazo por estado", hover_data={"pedidos": True, "prazo": True},
                 labels={"no_prazo": "% no prazo", "customer_state": "", "prazo": "Prazo mediano (dias)"},
                 color="no_prazo", color_continuous_scale="RdYlGn", range_color=[75, 100])
    fig.update_layout(plot_bgcolor="white", coloraxis_showscale=False, height=650)
    col_b.plotly_chart(fig, use_container_width=True)

# ── Vendedores ────────────────────────────────────────────────────────────────

with aba_vendedores:
    vendedores = dados["vendedores"]
    avaliados = vendedores.dropna(subset=["score"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Vendedores", f"{len(vendedores):,}".replace(",", "."))
    c2.metric("Com score (20+ pedidos)", f"{len(avaliados):,}".replace(",", "."))
    c3.metric("Inativos há 90+ dias", f"{vendedores['inativo'].mean():.1%}".replace(".", ","))

    st.markdown("Score = 40% nota média + 40% pontualidade + 20% volume, em percentis entre vendedores com 20+ pedidos.")

    fig = px.scatter(avaliados, x="taxa_no_prazo", y="nota_media", size="pedidos", color="score",
                     color_continuous_scale="RdYlGn", hover_data={"seller_state": True, "receita": ":,.0f"},
                     title="Pontualidade × nota (tamanho = pedidos)",
                     labels={"taxa_no_prazo": "% no prazo", "nota_media": "Nota média", "seller_state": "UF"})
    fig.update_layout(plot_bgcolor="white", xaxis_tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

    estados_vend = sorted(avaliados["seller_state"].dropna().unique())
    uf = st.selectbox("Estado do vendedor", ["Todos"] + estados_vend)
    tabela = avaliados if uf == "Todos" else avaliados[avaliados["seller_state"] == uf]
    colunas = ["seller_id", "seller_city", "seller_state", "pedidos", "receita", "nota_media",
               "taxa_no_prazo", "taxa_postagem_atrasada", "score"]
    formato = {"pedidos": "{:,.0f}", "receita": "R$ {:,.0f}", "nota_media": "{:.2f}", "taxa_no_prazo": "{:.1%}",
               "taxa_postagem_atrasada": "{:.1%}", "score": "{:.1f}"}

    col_a, col_b = st.columns(2)
    col_a.subheader("Melhores pelo score")
    col_a.dataframe(tabela.nlargest(15, "score")[colunas].style.format(formato), hide_index=True, use_container_width=True)
    col_b.subheader("Piores pelo score")
    col_b.dataframe(tabela.nsmallest(15, "score")[colunas].style.format(formato), hide_index=True, use_container_width=True)
