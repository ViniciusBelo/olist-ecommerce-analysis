"""Carregamento e validação dos datasets brutos da Olist."""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional
import warnings

from src.config import RAW_FILES


def load_raw_dataset(name: str, nrows: Optional[int] = None) -> pd.DataFrame:
    """Carrega um dataset bruto pelo nome definido em config.RAW_FILES."""
    path = RAW_FILES.get(name)
    if path is None:
        raise KeyError(f"Dataset '{name}' não encontrado. Opções: {list(RAW_FILES.keys())}")
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {path}\n"
            "Faça o download em: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce\n"
            "e coloque os CSVs em data/raw/"
        )
    return pd.read_csv(path, nrows=nrows, low_memory=False)


def load_all_raw() -> Dict[str, pd.DataFrame]:
    """Carrega todos os datasets brutos disponíveis em RAW_FILES."""
    datasets = {}
    for name in RAW_FILES:
        try:
            datasets[name] = load_raw_dataset(name)
            print(f"  ✓ {name:<35} {datasets[name].shape[0]:>7,} linhas × {datasets[name].shape[1]} colunas")
        except FileNotFoundError as e:
            warnings.warn(str(e))
    return datasets


def validate_datasets(datasets: Dict[str, pd.DataFrame]) -> bool:
    """Verifica integridade básica dos datasets carregados."""
    required = ["orders", "order_items", "customers", "products", "sellers", "order_payments"]
    missing = [r for r in required if r not in datasets]
    if missing:
        raise ValueError(f"Datasets obrigatórios ausentes: {missing}")

    # Validações de chaves primárias
    checks = [
        ("orders", "order_id"),
        ("customers", "customer_id"),
        ("products", "product_id"),
        ("sellers", "seller_id"),
    ]
    all_ok = True
    for table, pk in checks:
        if table in datasets:
            dupes = datasets[table][pk].duplicated().sum()
            if dupes > 0:
                warnings.warn(f"  ⚠ {table}.{pk}: {dupes} duplicatas encontradas")
                all_ok = False
            else:
                print(f"  ✓ {table}.{pk}: sem duplicatas")

    return all_ok


def get_dataset_info(datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Retorna um DataFrame resumo com informações de cada dataset."""
    info = []
    for name, df in datasets.items():
        info.append({
            "dataset": name,
            "linhas": df.shape[0],
            "colunas": df.shape[1],
            "nulos_total": df.isnull().sum().sum(),
            "pct_nulos": f"{(df.isnull().sum().sum() / df.size * 100):.2f}%",
            "memoria_mb": f"{df.memory_usage(deep=True).sum() / 1024**2:.2f}",
        })
    return pd.DataFrame(info).set_index("dataset")
