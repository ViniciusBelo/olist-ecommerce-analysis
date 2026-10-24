"""Testes das funções de limpeza e enriquecimento com dados pequenos montados à mão."""

import pandas as pd
import pytest

from src.data_cleaner import (
    build_orders_enriched,
    cast_dates,
    clean_order_items,
    clean_order_payments,
    clean_order_reviews,
    clean_orders,
    clean_products,
)


@pytest.fixture
def datasets():
    orders = pd.DataFrame({
        "order_id": ["o1", "o2", "o3"],
        "customer_id": ["c1", "c2", "c3"],
        "order_status": ["delivered", "delivered", "canceled"],
        "order_purchase_timestamp": ["2018-01-01 10:00:00", "2018-01-05 15:30:00", "2018-01-07 09:00:00"],
        "order_approved_at": ["2018-01-01 11:00:00", "2018-01-05 16:00:00", None],
        "order_delivered_carrier_date": ["2018-01-02 10:00:00", "2018-01-08 10:00:00", None],
        "order_delivered_customer_date": ["2018-01-06 10:00:00", "2018-01-25 10:00:00", None],
        "order_estimated_delivery_date": ["2018-01-15 00:00:00", "2018-01-20 00:00:00", "2018-01-30 00:00:00"],
    })
    order_items = pd.DataFrame({
        "order_id": ["o1", "o1", "o2", "o3"],
        "order_item_id": [1, 2, 1, 1],
        "product_id": ["p1", "p2", "p1", "p2"],
        "seller_id": ["s1", "s2", "s1", "s2"],
        "shipping_limit_date": ["2018-01-03 00:00:00"] * 4,
        "price": [100.0, 50.0, 100.0, 30.0],
        "freight_value": [10.0, 5.0, 12.0, 8.0],
    })
    order_payments = pd.DataFrame({
        "order_id": ["o1", "o1", "o2", "o3"],
        "payment_sequential": [1, 2, 1, 1],
        "payment_type": ["credit_card", "voucher", "boleto", "credit_card"],
        "payment_installments": [3, 1, 1, 2],
        "payment_value": [140.0, 25.0, 112.0, 38.0],
    })
    order_reviews = pd.DataFrame({
        "review_id": ["r1", "r2", "r3"],
        "order_id": ["o1", "o2", "o2"],
        "review_score": [5, 1, 3],
        "review_comment_message": [None, "atrasou", "chegou"],
        "review_creation_date": ["2018-01-07", "2018-01-26", "2018-01-28"],
        "review_answer_timestamp": ["2018-01-08", "2018-01-27", "2018-01-29"],
    })
    customers = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3"],
        "customer_unique_id": ["u1", "u2", "u1"],
        "customer_zip_code_prefix": [1000, 2000, 1000],
        "customer_city": ["sao paulo", "rio de janeiro", "sao paulo"],
        "customer_state": ["SP", "RJ", "SP"],
    })
    products = pd.DataFrame({
        "product_id": ["p1", "p2"],
        "product_category_name": ["beleza_saude", "esporte_lazer"],
        "product_weight_g": [500.0, None],
        "product_length_cm": [20.0, 30.0],
        "product_height_cm": [10.0, 15.0],
        "product_width_cm": [15.0, 20.0],
    })
    translation = pd.DataFrame({
        "product_category_name": ["beleza_saude", "esporte_lazer"],
        "product_category_name_english": ["health_beauty", "sports_leisure"],
    })
    return {
        "orders": orders,
        "order_items": order_items,
        "order_payments": order_payments,
        "order_reviews": order_reviews,
        "customers": customers,
        "products": products,
        "sellers": pd.DataFrame({"seller_id": ["s1", "s2"], "seller_state": ["SP", "MG"]}),
        "product_category_translation": translation,
    }


def test_cast_dates_converte_e_transforma_invalidos_em_nat():
    df = pd.DataFrame({"data": ["2018-01-01", "não é data"], "outra": [1, 2]})
    resultado = cast_dates(df, ["data", "coluna_inexistente"])
    assert pd.api.types.is_datetime64_any_dtype(resultado["data"])
    assert pd.isna(resultado.loc[1, "data"])


def test_clean_orders_remove_pedidos_sem_data_e_cria_colunas_de_tempo(datasets):
    orders = datasets["orders"].copy()
    orders.loc[2, "order_purchase_timestamp"] = None
    resultado = clean_orders(orders)
    assert len(resultado) == 2
    assert resultado.loc[0, "purchase_hour"] == 10
    assert resultado.loc[0, "purchase_day_of_week"] == "Monday"


def test_clean_order_items_soma_preco_e_frete(datasets):
    resultado = clean_order_items(datasets["order_items"].copy())
    assert resultado["total_item_value"].tolist() == [110.0, 55.0, 112.0, 38.0]


def test_clean_order_payments_agrega_um_registro_por_pedido(datasets):
    resultado = clean_order_payments(datasets["order_payments"].copy()).set_index("order_id")
    assert len(resultado) == 3
    assert resultado.loc["o1", "payment_value"] == 165.0
    assert resultado.loc["o1", "payment_installments"] == 3
    assert resultado.loc["o1", "n_payment_types"] == 2


def test_clean_order_reviews_mantem_a_review_mais_recente(datasets):
    resultado = clean_order_reviews(datasets["order_reviews"].copy()).set_index("order_id")
    assert len(resultado) == 2
    assert resultado.loc["o2", "review_score"] == 3
    assert not resultado.loc["o1", "has_comment"]


def test_clean_products_traduz_categoria_e_preenche_peso(datasets):
    resultado = clean_products(datasets["products"].copy(), datasets["product_category_translation"].copy())
    assert set(resultado["product_category_name_english"]) == {"health_beauty", "sports_leisure"}
    assert resultado["product_weight_g"].notna().all()


def test_build_orders_enriched_uma_linha_por_pedido(datasets):
    resultado = build_orders_enriched(datasets)
    assert len(resultado) == len(datasets["orders"])
    assert resultado["order_id"].is_unique


def test_build_orders_enriched_calcula_receita_e_metricas_de_entrega(datasets):
    resultado = build_orders_enriched(datasets).set_index("order_id")

    assert resultado.loc["o1", "revenue"] == 150.0
    assert resultado.loc["o1", "n_items"] == 2

    # o1: entregue em 5 dias, prazo de 13 → adiantado
    assert resultado.loc["o1", "delivery_days"] == 5
    assert resultado.loc["o1", "delivery_delay_days"] == 5 - 13
    assert resultado.loc["o1", "delivered_on_time"]

    # o2: entregue em 19 dias, prazo de 14 → atrasado
    assert resultado.loc["o2", "delivery_delay_days"] == 19 - 14
    assert not resultado.loc["o2", "delivered_on_time"]

    # o3 cancelado não tem entrega
    assert not resultado.loc["o3", "is_delivered"]
    assert pd.isna(resultado.loc["o3", "delivery_days"])


def test_build_orders_enriched_usa_customer_unique_id(datasets):
    resultado = build_orders_enriched(datasets)
    # c1 e c3 são a mesma pessoa
    assert resultado.groupby("customer_unique_id")["order_id"].count().to_dict() == {"u1": 2, "u2": 1}
