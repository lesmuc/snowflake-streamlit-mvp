"""Data transformation and KPI calculation for the MENU dataset."""

from __future__ import annotations

import numpy as np
import pandas as pd


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce types, drop incomplete rows, and add derived columns.

    Adds:
    - ``profit_usd``: sale_price_usd − cost_of_goods_usd
    - ``margin_pct``: (profit_usd / sale_price_usd) × 100, NaN when price is 0

    Returns a fresh DataFrame; the input is not modified.
    """
    df = df.copy()

    # Coerce numeric columns — Snowflake connector usually returns Decimal objects
    for col in ("cost_of_goods_usd", "sale_price_usd"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows where price or cost is missing
    df = df.dropna(subset=["sale_price_usd", "cost_of_goods_usd"])

    # Derived columns (only if not already present from SQL)
    if "profit_usd" not in df.columns:
        df["profit_usd"] = df["sale_price_usd"] - df["cost_of_goods_usd"]

    if "margin_pct" not in df.columns:
        df["margin_pct"] = np.where(
            df["sale_price_usd"] == 0,
            np.nan,
            (df["profit_usd"] / df["sale_price_usd"]) * 100,
        )

    df["profit_usd"] = pd.to_numeric(df["profit_usd"], errors="coerce")
    df["margin_pct"] = pd.to_numeric(df["margin_pct"], errors="coerce")

    return df.reset_index(drop=True)


def calc_kpis(df: pd.DataFrame) -> dict:
    """Compute summary KPIs from a cleaned MENU DataFrame.

    Returns a dict with:
    - ``item_count``: number of rows
    - ``avg_sale_price``: mean sale_price_usd
    - ``avg_cost``: mean cost_of_goods_usd
    - ``avg_margin_pct``: mean margin_pct (ignores NaN)
    """
    if df.empty:
        return {
            "item_count": 0,
            "avg_sale_price": 0.0,
            "avg_cost": 0.0,
            "avg_margin_pct": 0.0,
        }

    return {
        "item_count": len(df),
        "avg_sale_price": float(df["sale_price_usd"].mean()),
        "avg_cost": float(df["cost_of_goods_usd"].mean()),
        "avg_margin_pct": float(df["margin_pct"].mean(skipna=True)),
    }


def top_items(
    df: pd.DataFrame,
    by: str = "profit_usd",
    top_n: int = 10,
) -> pd.DataFrame:
    """Return up to *top_n* rows sorted descending by *by*.

    *by* should be ``"profit_usd"`` or ``"margin_pct"``.
    Safe when *top_n* exceeds the number of available rows.
    """
    if df.empty:
        return df

    sort_col = by if by in df.columns else "profit_usd"
    n = min(top_n, len(df))
    return (
        df.sort_values(sort_col, ascending=False)
        .head(n)
        .reset_index(drop=True)
    )


def profit_by_group(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Aggregate profit metrics grouped by *group_col*.

    Returns a DataFrame with columns:
    - the group column
    - ``item_count``
    - ``avg_profit_usd``
    - ``avg_margin_pct``
    - ``total_profit_usd``

    Sorted descending by ``avg_margin_pct``.
    """
    if df.empty or group_col not in df.columns:
        cols = [group_col, "item_count", "avg_profit_usd", "avg_margin_pct", "total_profit_usd"]
        return pd.DataFrame(columns=cols)

    agg = (
        df.groupby(group_col)
        .agg(
            item_count=("profit_usd", "count"),
            avg_profit_usd=("profit_usd", "mean"),
            total_profit_usd=("profit_usd", "sum"),
            avg_margin_pct=("margin_pct", "mean"),
        )
        .reset_index()
        .sort_values("avg_margin_pct", ascending=False)
        .reset_index(drop=True)
    )
    return agg
