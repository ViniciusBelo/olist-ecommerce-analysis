"""Configurações centralizadas do projeto."""

from pathlib import Path

# ── Diretórios ────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# ── Arquivos brutos esperados ─────────────────────────────────────────────────
RAW_FILES = {
    "orders": RAW_DIR / "olist_orders_dataset.csv",
    "order_items": RAW_DIR / "olist_order_items_dataset.csv",
    "order_payments": RAW_DIR / "olist_order_payments_dataset.csv",
    "order_reviews": RAW_DIR / "olist_order_reviews_dataset.csv",
    "customers": RAW_DIR / "olist_customers_dataset.csv",
    "products": RAW_DIR / "olist_products_dataset.csv",
    "sellers": RAW_DIR / "olist_sellers_dataset.csv",
    "geolocation": RAW_DIR / "olist_geolocation_dataset.csv",
    "product_category_translation": RAW_DIR / "product_category_name_translation.csv",
}

# ── Arquivos processados ──────────────────────────────────────────────────────
PROCESSED_FILES = {
    "orders_enriched": PROCESSED_DIR / "orders_enriched.parquet",
    "rfm": PROCESSED_DIR / "rfm_segments.parquet",
    "delivery": PROCESSED_DIR / "delivery_analysis.parquet",
    "seller_performance": PROCESSED_DIR / "seller_performance.parquet",
}

# ── Parâmetros de análise ─────────────────────────────────────────────────────
# Data de referência para cálculo de RFM (último pedido entregue + 1 dia)
RFM_REFERENCE_DATE = "2018-08-30"

# Número de clusters para segmentação K-Means
N_CLUSTERS_RFM = 4

# Paleta de cores do projeto
COLORS = {
    "primary": "#2E86AB",
    "secondary": "#A23B72",
    "accent": "#F18F01",
    "success": "#C73E1D",
    "neutral": "#3B1F2B",
    "palette": ["#2E86AB", "#A23B72", "#F18F01", "#44BBA4", "#E94F37"],
}

# ── Estilo de visualizações ───────────────────────────────────────────────────
PLOT_STYLE = "seaborn-v0_8-whitegrid"
FIGURE_DPI = 150
FIGURE_SIZE = (12, 6)
