"""Unit tests for processing/transform.py — no Snowflake connection required."""

from __future__ import annotations

from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from processing.transform import calc_kpis, clean, profit_by_group, top_items

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_df() -> pd.DataFrame:
    """Minimal MENU-like DataFrame for testing."""
    return pd.DataFrame(
        {
            "menu_item_name": ["Burger", "Ice Cream", "BBQ Ribs", "Salad", "Hot Dog"],
            "truck_brand_name": ["Brand A", "Brand B", "Brand A", "Brand C", "Brand B"],
            "item_category": ["Main", "Dessert", "Main", "Main", "Main"],
            "item_subcategory": ["Beef", "Frozen", "Pork", "Veg", "Pork"],
            "sale_price_usd": [10.0, 5.0, 15.0, 8.0, 6.0],
            "cost_of_goods_usd": [4.0, 2.0, 7.0, 3.0, 2.5],
        }
    )


@pytest.fixture()
def df_with_nulls() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "menu_item_name": ["Item A", "Item B", "Item C"],
            "truck_brand_name": ["Brand A", "Brand A", "Brand B"],
            "item_category": ["Main", "Main", "Dessert"],
            "item_subcategory": ["X", "Y", "Z"],
            "sale_price_usd": [10.0, None, 8.0],
            "cost_of_goods_usd": [4.0, 3.0, None],
        }
    )


@pytest.fixture()
def df_zero_price() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "menu_item_name": ["Free Item"],
            "truck_brand_name": ["Brand X"],
            "item_category": ["Main"],
            "item_subcategory": ["X"],
            "sale_price_usd": [0.0],
            "cost_of_goods_usd": [1.0],
        }
    )


# ---------------------------------------------------------------------------
# clean()
# ---------------------------------------------------------------------------


def test_clean_adds_profit_column(sample_df):
    result = clean(sample_df)
    assert "profit_usd" in result.columns
    # Burger: 10 - 4 = 6
    burger_profit = result.loc[result["menu_item_name"] == "Burger", "profit_usd"].iloc[0]
    assert burger_profit == pytest.approx(6.0)


def test_clean_adds_margin_pct(sample_df):
    result = clean(sample_df)
    assert "margin_pct" in result.columns
    # Burger: (6/10)*100 = 60%
    burger_margin = result.loc[result["menu_item_name"] == "Burger", "margin_pct"].iloc[0]
    assert burger_margin == pytest.approx(60.0)


def test_clean_drops_nulls(df_with_nulls):
    result = clean(df_with_nulls)
    # Item B has NULL sale_price, Item C has NULL cost → both dropped
    assert len(result) == 1
    assert result["menu_item_name"].iloc[0] == "Item A"


def test_clean_zero_price_yields_nan_margin(df_zero_price):
    result = clean(df_zero_price)
    assert result["profit_usd"].iloc[0] == pytest.approx(-1.0)
    assert np.isnan(result["margin_pct"].iloc[0])


def test_clean_does_not_modify_input(sample_df):
    original_cols = list(sample_df.columns)
    clean(sample_df)
    assert list(sample_df.columns) == original_cols


# ---------------------------------------------------------------------------
# calc_kpis()
# ---------------------------------------------------------------------------


def test_calc_kpis_counts(sample_df):
    result = calc_kpis(clean(sample_df))
    assert result["item_count"] == 5


def test_calc_kpis_avg_margin(sample_df):
    df = clean(sample_df)
    result = calc_kpis(df)
    expected_avg_margin = df["margin_pct"].mean()
    assert result["avg_margin_pct"] == pytest.approx(expected_avg_margin, rel=1e-4)


def test_calc_kpis_empty_df():
    empty = pd.DataFrame(columns=["sale_price_usd", "cost_of_goods_usd", "margin_pct"])
    result = calc_kpis(empty)
    assert result["item_count"] == 0
    assert result["avg_margin_pct"] == 0.0


# ---------------------------------------------------------------------------
# top_items()
# ---------------------------------------------------------------------------


def test_top_items_limit(sample_df):
    df = clean(sample_df)
    result = top_items(df, by="profit_usd", top_n=3)
    assert len(result) == 3


def test_top_items_sorting(sample_df):
    df = clean(sample_df)
    result = top_items(df, by="profit_usd", top_n=5)
    # Should be descending
    profits = result["profit_usd"].tolist()
    assert profits == sorted(profits, reverse=True)


def test_top_items_limit_exceeds_rows(sample_df):
    df = clean(sample_df)
    result = top_items(df, by="profit_usd", top_n=100)
    assert len(result) == len(df)


def test_top_items_sort_by_margin(sample_df):
    df = clean(sample_df)
    result = top_items(df, by="margin_pct", top_n=5)
    margins = result["margin_pct"].dropna().tolist()
    assert margins == sorted(margins, reverse=True)


# ---------------------------------------------------------------------------
# profit_by_group()
# ---------------------------------------------------------------------------


def test_profit_by_group_aggregation(sample_df):
    df = clean(sample_df)
    result = profit_by_group(df, "truck_brand_name")
    assert "truck_brand_name" in result.columns
    assert "avg_profit_usd" in result.columns
    assert "item_count" in result.columns
    # Brand A has 2 items (Burger + BBQ Ribs)
    brand_a = result.loc[result["truck_brand_name"] == "Brand A"]
    assert brand_a["item_count"].iloc[0] == 2


def test_profit_by_group_sorted_descending(sample_df):
    df = clean(sample_df)
    result = profit_by_group(df, "truck_brand_name")
    margins = result["avg_margin_pct"].tolist()
    assert margins == sorted(margins, reverse=True)


def test_profit_by_group_unknown_column(sample_df):
    df = clean(sample_df)
    result = profit_by_group(df, "nonexistent_column")
    assert result.empty


def test_profit_by_group_empty_df():
    empty = pd.DataFrame(columns=["truck_brand_name", "profit_usd", "margin_pct"])
    result = profit_by_group(empty, "truck_brand_name")
    assert result.empty


def test_profit_by_group_total_profit(sample_df):
    df = clean(sample_df)
    result = profit_by_group(df, "truck_brand_name")
    # Brand A: Burger profit=6, BBQ Ribs profit=8 → total=14
    brand_a = result.loc[result["truck_brand_name"] == "Brand A"]
    assert brand_a["total_profit_usd"].iloc[0] == pytest.approx(14.0)


def test_profit_by_group_avg_profit(sample_df):
    df = clean(sample_df)
    result = profit_by_group(df, "truck_brand_name")
    # Brand A: avg profit = (6+8)/2 = 7
    brand_a = result.loc[result["truck_brand_name"] == "Brand A"]
    assert brand_a["avg_profit_usd"].iloc[0] == pytest.approx(7.0)


def test_profit_by_group_by_category(sample_df):
    df = clean(sample_df)
    result = profit_by_group(df, "item_category")
    assert "item_category" in result.columns
    # Dessert has 1 item (Ice Cream)
    dessert = result.loc[result["item_category"] == "Dessert"]
    assert dessert["item_count"].iloc[0] == 1


# ---------------------------------------------------------------------------
# clean() — additional edge cases
# ---------------------------------------------------------------------------


def test_clean_decimal_objects_are_coerced():
    """Snowflake connector returns decimal.Decimal — clean() must handle them."""
    df = pd.DataFrame(
        {
            "menu_item_name": ["Burger"],
            "truck_brand_name": ["Brand A"],
            "item_category": ["Main"],
            "item_subcategory": ["Beef"],
            "sale_price_usd": [Decimal("10.00")],
            "cost_of_goods_usd": [Decimal("4.00")],
        }
    )
    result = clean(df)
    assert result["profit_usd"].iloc[0] == pytest.approx(6.0)
    assert result["margin_pct"].iloc[0] == pytest.approx(60.0)


def test_clean_precomputed_profit_not_overwritten():
    """If profit_usd already exists (from SQL), clean() must not recalculate it."""
    df = pd.DataFrame(
        {
            "menu_item_name": ["Burger"],
            "truck_brand_name": ["Brand A"],
            "item_category": ["Main"],
            "item_subcategory": ["Beef"],
            "sale_price_usd": [10.0],
            "cost_of_goods_usd": [4.0],
            "profit_usd": [99.0],  # sentinel — should be preserved
        }
    )
    result = clean(df)
    assert result["profit_usd"].iloc[0] == pytest.approx(99.0)


def test_clean_precomputed_margin_not_overwritten():
    """If margin_pct already exists (from SQL), clean() must not recalculate it."""
    df = pd.DataFrame(
        {
            "menu_item_name": ["Burger"],
            "truck_brand_name": ["Brand A"],
            "item_category": ["Main"],
            "item_subcategory": ["Beef"],
            "sale_price_usd": [10.0],
            "cost_of_goods_usd": [4.0],
            "profit_usd": [6.0],
            "margin_pct": [42.0],  # sentinel — should be preserved
        }
    )
    result = clean(df)
    assert result["margin_pct"].iloc[0] == pytest.approx(42.0)


def test_clean_resets_index(df_with_nulls):
    """Index must be contiguous 0..n after dropping null rows."""
    result = clean(df_with_nulls)
    assert list(result.index) == list(range(len(result)))


def test_clean_all_nulls_returns_empty():
    df = pd.DataFrame(
        {
            "menu_item_name": ["A", "B"],
            "truck_brand_name": ["X", "X"],
            "item_category": ["Main", "Main"],
            "item_subcategory": ["X", "X"],
            "sale_price_usd": [None, None],
            "cost_of_goods_usd": [None, None],
        }
    )
    result = clean(df)
    assert result.empty


# ---------------------------------------------------------------------------
# calc_kpis() — additional checks
# ---------------------------------------------------------------------------


def test_calc_kpis_avg_sale_price(sample_df):
    df = clean(sample_df)
    result = calc_kpis(df)
    expected = df["sale_price_usd"].mean()
    assert result["avg_sale_price"] == pytest.approx(expected, rel=1e-4)


def test_calc_kpis_avg_cost(sample_df):
    df = clean(sample_df)
    result = calc_kpis(df)
    expected = df["cost_of_goods_usd"].mean()
    assert result["avg_cost"] == pytest.approx(expected, rel=1e-4)


def test_calc_kpis_single_row():
    df = clean(
        pd.DataFrame(
            {
                "menu_item_name": ["Solo"],
                "truck_brand_name": ["Brand X"],
                "item_category": ["Main"],
                "item_subcategory": ["X"],
                "sale_price_usd": [20.0],
                "cost_of_goods_usd": [5.0],
            }
        )
    )
    result = calc_kpis(df)
    assert result["item_count"] == 1
    assert result["avg_sale_price"] == pytest.approx(20.0)
    assert result["avg_margin_pct"] == pytest.approx(75.0)


def test_calc_kpis_ignores_nan_margin():
    """avg_margin_pct must skip NaN rows (zero-price items)."""
    df = clean(
        pd.DataFrame(
            {
                "menu_item_name": ["Paid", "Free"],
                "truck_brand_name": ["B", "B"],
                "item_category": ["Main", "Main"],
                "item_subcategory": ["X", "X"],
                "sale_price_usd": [10.0, 0.0],
                "cost_of_goods_usd": [4.0, 1.0],
            }
        )
    )
    result = calc_kpis(df)
    # Only the Paid item contributes to avg_margin_pct
    assert result["avg_margin_pct"] == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# top_items() — additional edge cases
# ---------------------------------------------------------------------------


def test_top_items_empty_df():
    empty = pd.DataFrame(columns=["profit_usd", "margin_pct"])
    result = top_items(empty, by="profit_usd", top_n=5)
    assert result.empty


def test_top_items_invalid_sort_col_falls_back(sample_df):
    """Unknown sort column must fall back to profit_usd without raising."""
    df = clean(sample_df)
    result = top_items(df, by="nonexistent", top_n=5)
    profits = result["profit_usd"].tolist()
    assert profits == sorted(profits, reverse=True)


def test_top_items_top_n_one(sample_df):
    df = clean(sample_df)
    result = top_items(df, by="profit_usd", top_n=1)
    assert len(result) == 1
    assert result["profit_usd"].iloc[0] == df["profit_usd"].max()
