"""Limpeza, tipagem e enriquecimento dos datasets Olist."""

import pandas as pd
import numpy as np
from typing import Dict

from src.config import PROCESSED_FILES


# ── Colunas de data por dataset ───────────────────────────────────────────────
DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
    "order_items": ["shipping_limit_date"],
}


def cast_dates(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Converte colunas de string para datetime, coercindo erros."""
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = cast_dates(df, DATE_COLUMNS["orders"])
    # Remove pedidos sem data de compra (impossível analisar)
    df = df.dropna(subset=["order_purchase_timestamp"])
    # Colunas de engenharia de tempo úteis
    df["purchase_year"] = df["order_purchase_timestamp"].dt.year
    df["purchase_month"] = df["order_purchase_timestamp"].dt.month
    df["purchase_day_of_week"] = df["order_purchase_timestamp"].dt.day_name()
    df["purchase_hour"] = df["order_purchase_timestamp"].dt.hour
    df["purchase_quarter"] = df["order_purchase_timestamp"].dt.quarter
    return df


def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:
    df = cast_dates(df, DATE_COLUMNS["order_items"])
    df["total_item_value"] = df["price"] + df["freight_value"]
    return df


def clean_order_payments(df: pd.DataFrame) -> pd.DataFrame:
    # Agrega pagamentos por pedido (pode haver múltiplos por parcelamento)
    agg = (
        df.groupby("order_id")
        .agg(
            payment_type=("payment_type", lambda x: x.mode()[0]),
            payment_installments=("payment_installments", "max"),
            payment_value=("payment_value", "sum"),
            n_payment_types=("payment_type", "nunique"),
        )
        .reset_index()
    )
    return agg


def clean_order_reviews(df: pd.DataFrame) -> pd.DataFrame:
    df = cast_dates(df, DATE_COLUMNS["order_reviews"])
    df["review_comment_length"] = df["review_comment_message"].fillna("").str.len()
    df["has_comment"] = df["review_comment_message"].notna()
    # Mantém apenas 1 review por pedido (o mais recente)
    df = df.sort_values("review_answer_timestamp").drop_duplicates(
        subset="order_id", keep="last"
    )
    return df


def clean_products(df: pd.DataFrame, translation: pd.DataFrame) -> pd.DataFrame:
    df = df.merge(translation, on="product_category_name", how="left")
    df["product_category_name_english"] = df["product_category_name_english"].fillna(
        df["product_category_name"]
    )
    # Preenche dimensões ausentes com mediana por categoria
    for col in ["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]:
        if col in df.columns:
            median_by_cat = df.groupby("product_category_name_english")[col].transform("median")
            df[col] = df[col].fillna(median_by_cat).fillna(df[col].median())
    return df


def build_orders_enriched(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Constrói o dataset central enriquecido com todas as dimensões relevantes.
    Este é o 'fact table' do projeto.
    """
    orders = clean_orders(datasets["orders"].copy())
    items = clean_order_items(datasets["order_items"].copy())
    payments = clean_order_payments(datasets["order_payments"].copy())
    reviews = clean_order_reviews(datasets["order_reviews"].copy())
    products = clean_products(
        datasets["products"].copy(), datasets["product_category_translation"].copy()
    )
    customers = datasets["customers"].copy()
    sellers = datasets["sellers"].copy()

    # Agrega itens por pedido
    items_agg = (
        items.groupby("order_id")
        .agg(
            n_items=("order_item_id", "count"),
            revenue=("price", "sum"),
            freight=("freight_value", "sum"),
            total_order_value=("total_item_value", "sum"),
            n_distinct_products=("product_id", "nunique"),
            n_distinct_sellers=("seller_id", "nunique"),
        )
        .reset_index()
    )

    # Categoria do produto principal por pedido
    product_cat = (
        items.merge(products[["product_id", "product_category_name_english"]], on="product_id", how="left")
        .groupby("order_id")["product_category_name_english"]
        .agg(lambda x: x.mode()[0] if not x.mode().empty else "unknown")
        .reset_index()
        .rename(columns={"product_category_name_english": "main_category"})
    )

    # Mescla tudo
    df = (
        orders
        .merge(items_agg, on="order_id", how="left")
        .merge(product_cat, on="order_id", how="left")
        .merge(payments, on="order_id", how="left")
        .merge(reviews[["order_id", "review_score", "has_comment", "review_comment_length"]], on="order_id", how="left")
        .merge(customers[["customer_id", "customer_unique_id", "customer_city", "customer_state"]], on="customer_id", how="left")
    )

    # Métricas de entrega
    df["delivery_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days

    df["days_to_estimated"] = (
        df["order_estimated_delivery_date"] - df["order_purchase_timestamp"]
    ).dt.days

    df["delivery_delay_days"] = df["delivery_days"] - df["days_to_estimated"]
    df["delivered_on_time"] = df["delivery_delay_days"] <= 0

    # Apenas pedidos entregues para análises de entrega
    df["is_delivered"] = df["order_status"] == "delivered"

    return df


def save_processed(df: pd.DataFrame, name: str) -> None:
    path = PROCESSED_FILES[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"  ✓ Salvo: {path} ({df.shape[0]:,} linhas)")


def load_processed(name: str) -> pd.DataFrame:
    path = PROCESSED_FILES[name]
    if not path.exists():
        raise FileNotFoundError(f"Execute o notebook de limpeza primeiro. Arquivo esperado: {path}")
    return pd.read_parquet(path)
