"""Parametrized SQL queries against the Tasty Bytes MENU table."""

from __future__ import annotations

import pandas as pd

from data.snowflake_client import SnowflakeClient


def query_all_menu(
    client: SnowflakeClient,
    brands: list[str] | None = None,
    categories: list[str] | None = None,
    subcategories: list[str] | None = None,
) -> pd.DataFrame:
    """Return all MENU rows with calculated profit/margin columns.

    Optional filters are applied via IN-clauses when provided.
    """
    where_clauses = []
    params: dict = {}

    if brands:
        placeholders = ", ".join(f"%(brand_{i})s" for i in range(len(brands)))
        where_clauses.append(f"truck_brand_name IN ({placeholders})")
        for i, b in enumerate(brands):
            params[f"brand_{i}"] = b

    if categories:
        placeholders = ", ".join(f"%(cat_{i})s" for i in range(len(categories)))
        where_clauses.append(f"item_category IN ({placeholders})")
        for i, c in enumerate(categories):
            params[f"cat_{i}"] = c

    if subcategories:
        placeholders = ", ".join(f"%(subcat_{i})s" for i in range(len(subcategories)))
        where_clauses.append(f"item_subcategory IN ({placeholders})")
        for i, s in enumerate(subcategories):
            params[f"subcat_{i}"] = s

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    sql = f"""
        SELECT
            menu_id,
            menu_type_id,
            menu_type,
            truck_brand_name,
            menu_item_id,
            menu_item_name,
            item_category,
            item_subcategory,
            cost_of_goods_usd,
            sale_price_usd,
            (sale_price_usd - cost_of_goods_usd)                       AS profit_usd,
            CASE
                WHEN sale_price_usd = 0 THEN NULL
                ELSE ((sale_price_usd - cost_of_goods_usd) / sale_price_usd) * 100
            END                                                         AS margin_pct
        FROM {client.schema}.menu
        {where_sql}
        ORDER BY menu_item_name
    """
    return client.run_query(sql, params)


def query_filter_options(client: SnowflakeClient) -> dict[str, list[str]]:
    """Return distinct values for sidebar filter widgets."""
    sql = f"""
        SELECT
            truck_brand_name,
            item_category,
            item_subcategory
        FROM {client.schema}.menu
        ORDER BY truck_brand_name, item_category, item_subcategory
    """
    df = client.run_query(sql)
    return {
        "brands": sorted(df["truck_brand_name"].dropna().unique().tolist()),
        "categories": sorted(df["item_category"].dropna().unique().tolist()),
        "subcategories": sorted(df["item_subcategory"].dropna().unique().tolist()),
    }


def query_profit_by_brand(client: SnowflakeClient) -> pd.DataFrame:
    """Aggregate profit/margin metrics grouped by truck brand."""
    sql = f"""
        SELECT
            truck_brand_name,
            COUNT(*)                                                       AS item_count,
            ROUND(AVG(sale_price_usd - cost_of_goods_usd), 4)             AS avg_profit_usd,
            ROUND(SUM(sale_price_usd - cost_of_goods_usd), 4)             AS total_profit_usd,
            ROUND(
                AVG(
                    CASE
                        WHEN sale_price_usd = 0 THEN NULL
                        ELSE ((sale_price_usd - cost_of_goods_usd) / sale_price_usd) * 100
                    END
                ), 2
            )                                                              AS avg_margin_pct
        FROM {client.schema}.menu
        GROUP BY truck_brand_name
        ORDER BY avg_margin_pct DESC
    """
    return client.run_query(sql)


def query_items_by_category(client: SnowflakeClient) -> pd.DataFrame:
    """Count menu items per category (and subcategory)."""
    sql = f"""
        SELECT
            item_category,
            item_subcategory,
            COUNT(*) AS item_count
        FROM {client.schema}.menu
        GROUP BY item_category, item_subcategory
        ORDER BY item_count DESC
    """
    return client.run_query(sql)


def query_ingredients(
    client: SnowflakeClient,
    menu_item_name: str | None = None,
) -> pd.DataFrame:
    """Flatten the VARIANT health-metrics object to extract ingredients per item.

    Uses LATERAL FLATTEN on the nested ingredients array inside
    ``menu_item_health_metrics_obj``.
    """
    where_sql = ""
    params: dict = {}
    if menu_item_name:
        where_sql = "WHERE m.menu_item_name = %(item_name)s"
        params["item_name"] = menu_item_name

    sql = f"""
        SELECT
            m.menu_item_name,
            m.truck_brand_name,
            m.item_category,
            f.value::STRING AS ingredient
        FROM {client.schema}.menu AS m,
             LATERAL FLATTEN(
                 INPUT => m.menu_item_health_metrics_obj:menu_item_health_metrics[0]:ingredients
             ) AS f
        WHERE m.menu_item_health_metrics_obj IS NOT NULL
          {"AND " + where_sql.replace("WHERE ", "") if where_sql else ""}
        ORDER BY m.menu_item_name, f.index
    """
    return client.run_query(sql, params)
