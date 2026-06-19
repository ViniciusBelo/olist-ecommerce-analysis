"""Funções de visualização reutilizáveis com estilo padronizado."""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List

from src.config import COLORS, FIGURES_DIR, FIGURE_DPI, FIGURE_SIZE, PLOT_STYLE


def setup_style() -> None:
    """Aplica o estilo global do projeto nas figuras Matplotlib."""
    plt.style.use(PLOT_STYLE)
    plt.rcParams.update({
        "figure.dpi": FIGURE_DPI,
        "figure.figsize": FIGURE_SIZE,
        "font.family": "DejaVu Sans",
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def save_fig(fig_name: str, fig=None, tight: bool = True) -> Path:
    """Salva a figura atual ou a fornecida em reports/figures/."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{fig_name}.png"
    if fig is not None:
        fig.write_image(str(path))
    else:
        if tight:
            plt.tight_layout()
        plt.savefig(path, dpi=FIGURE_DPI, bbox_inches="tight", facecolor="white")
    print(f"  ✓ Figura salva: {path.name}")
    return path


def format_brl(value: float) -> str:
    """Formata valor em R$ brasileiro."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ── Plots Matplotlib / Seaborn ────────────────────────────────────────────────

def bar_chart(
    data: pd.Series,
    title: str,
    xlabel: str = "",
    ylabel: str = "",
    color: str = None,
    horizontal: bool = False,
    top_n: int = None,
    fmt_currency: bool = False,
) -> plt.Figure:
    """Bar chart simples com anotação de valores."""
    setup_style()
    if top_n:
        data = data.head(top_n)
    color = color or COLORS["primary"]

    fig, ax = plt.subplots()
    if horizontal:
        bars = ax.barh(data.index, data.values, color=color, alpha=0.85)
        for bar in bars:
            w = bar.get_width()
            label = format_brl(w) if fmt_currency else f"{w:,.0f}"
            ax.text(w * 1.01, bar.get_y() + bar.get_height() / 2, label, va="center", fontsize=8)
        ax.invert_yaxis()
    else:
        bars = ax.bar(data.index, data.values, color=color, alpha=0.85)
        for bar in bars:
            h = bar.get_height()
            label = format_brl(h) if fmt_currency else f"{h:,.0f}"
            ax.text(bar.get_x() + bar.get_width() / 2, h * 1.01, label, ha="center", fontsize=8)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    return fig


def time_series_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str = None,
    fmt_currency: bool = False,
) -> plt.Figure:
    """Gráfico de linha temporal com área sombreada."""
    setup_style()
    color = color or COLORS["primary"]
    fig, ax = plt.subplots()
    ax.plot(df[x], df[y], color=color, linewidth=2, marker="o", markersize=4)
    ax.fill_between(df[x], df[y], alpha=0.15, color=color)
    if fmt_currency:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: format_brl(x)))
    ax.set_title(title)
    plt.xticks(rotation=45, ha="right")
    return fig


def heatmap_chart(
    pivot: pd.DataFrame,
    title: str,
    fmt: str = ".0f",
    cmap: str = "YlOrRd",
) -> plt.Figure:
    """Heatmap de correlação ou distribuição."""
    setup_style()
    fig, ax = plt.subplots(figsize=(14, 6))
    sns.heatmap(pivot, annot=True, fmt=fmt, cmap=cmap, linewidths=0.5, ax=ax, cbar_kws={"shrink": 0.8})
    ax.set_title(title)
    return fig


# ── Plots Plotly (interativos) ────────────────────────────────────────────────

def plotly_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color_seq: List[str] = None,
    text_auto: bool = True,
) -> go.Figure:
    color_seq = color_seq or COLORS["palette"]
    fig = px.bar(df, x=x, y=y, title=title, color=x, color_discrete_sequence=color_seq, text_auto=text_auto)
    fig.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
    return fig


def plotly_map_br(
    df: pd.DataFrame,
    locations: str,
    color: str,
    title: str,
    labels: dict = None,
) -> go.Figure:
    """Choropleth mapa por estado brasileiro."""
    fig = px.choropleth(
        df,
        locations=locations,
        color=color,
        title=title,
        labels=labels or {},
        locationmode="geojson-id",
        color_continuous_scale="Blues",
        scope="south america",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(paper_bgcolor="white")
    return fig


def plotly_scatter_rfm(df: pd.DataFrame) -> go.Figure:
    """Scatter plot de segmentos RFM."""
    fig = px.scatter(
        df,
        x="recency",
        y="monetary",
        size="frequency",
        color="segment",
        title="Segmentação RFM de Clientes",
        labels={"recency": "Recência (dias)", "monetary": "Valor Monetário (R$)", "frequency": "Frequência"},
        color_discrete_sequence=COLORS["palette"],
        hover_data=["customer_unique_id"] if "customer_unique_id" in df.columns else None,
    )
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    return fig
