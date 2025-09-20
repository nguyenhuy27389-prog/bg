"""Utilities for loading product data from spreadsheet files."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Mapping

import pandas as pd

REQUIRED_COLUMNS = {"code", "name", "unit_price"}
OPTIONAL_COLUMNS = {"unit", "description"}


def _normalise_string(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _normalise_number(value: object) -> float:
    if value is None:
        raise ValueError("Missing numeric value")
    if isinstance(value, (int, float)):
        if pd.isna(value):
            raise ValueError("Missing numeric value")
        return float(value)

    text = str(value).strip()
    if not text:
        raise ValueError("Missing numeric value")
    return float(text.replace(",", ""))


def load_products(excel_path: str | Path, *, sheet_name: str | int | None = 0) -> List[Dict[str, object]]:
    """Load products from an Excel file.

    Parameters
    ----------
    excel_path:
        Path to the Excel file containing the product catalogue.
    sheet_name:
        Optional Excel sheet name or index. Defaults to the first sheet.

    Returns
    -------
    list of dict
        A list of normalised product dictionaries.

    Raises
    ------
    FileNotFoundError
        If the input file does not exist.
    ValueError
        When required columns are missing.
    """

    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Product file not found: {path}")

    dataframe = pd.read_excel(path, sheet_name=sheet_name)

    missing_columns = REQUIRED_COLUMNS - set(dataframe.columns)
    if missing_columns:
        raise ValueError(
            "The product catalogue is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    dataframe = dataframe.where(~dataframe.isna(), None)

    products: List[Dict[str, object]] = []
    for row in dataframe.to_dict(orient="records"):
        product: Dict[str, object] = {}
        product["code"] = _normalise_string(row.get("code"))
        product["name"] = _normalise_string(row.get("name"))
        product["unit_price"] = _normalise_number(row.get("unit_price"))

        if not product["code"] or not product["name"]:
            raise ValueError("Product entries must include both a code and a name")

        for column in OPTIONAL_COLUMNS:
            value = _normalise_string(row.get(column))
            if value is not None:
                product[column] = value

        extra_data = {
            key: value
            for key, value in row.items()
            if key not in REQUIRED_COLUMNS | OPTIONAL_COLUMNS and value is not None
        }
        if extra_data:
            product["extra"] = extra_data

        products.append(product)

    return products


def build_product_index(
    products: Iterable[Mapping[str, object]], *, key: str = "code"
) -> Dict[str, Mapping[str, object]]:
    """Build an index for quick product lookups by product code."""

    index: Dict[str, Mapping[str, object]] = {}
    for product in products:
        identifier = product.get(key)
        if not identifier:
            continue
        index[str(identifier)] = product
    return index
