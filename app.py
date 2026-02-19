"""Tasty Bytes Menu Analytics — Streamlit dashboard powered by Snowflake."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # Picks up .env in local dev; no-op on Streamlit Cloud

from data.queries import (  # noqa: E402
    query_all_menu,
    query_filter_options,
    query_ingredients,
    query_items_by_category,
    query_profit_by_brand,
)
from data.snowflake_client import SnowflakeClient  # noqa: E402
from processing.transform import calc_kpis, clean, profit_by_group, top_items  # noqa: E402

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Tasty Bytes Menu Analytics",
    page_icon="🍔",
    layout="wide",
)

st.title("🍔 Tasty Bytes — Menu Analytics")
st.caption("Snowflake · Tasty Bytes · MENU table")

# ---------------------------------------------------------------------------
# Snowflake client (singleton across reruns)
# ---------------------------------------------------------------------------


@st.cache_resource
def get_client() -> SnowflakeClient:
    client = SnowflakeClient()
    client.connect()
    return client


client = get_client()

# ---------------------------------------------------------------------------
# Cached data loaders
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300, show_spinner=False)
def load_filter_options() -> dict[str, list[str]]:
    return query_filter_options(client)


@st.cache_data(ttl=300, show_spinner=False)
def load_menu(
    brands: tuple[str, ...],
    categories: tuple[str, ...],
    subcategories: tuple[str, ...],
) -> pd.DataFrame:
    return query_all_menu(
        client,
        brands=list(brands) or None,
        categories=list(categories) or None,
        subcategories=list(subcategories) or None,
    )


@st.cache_data(ttl=300, show_spinner=False)
def load_profit_by_brand() -> pd.DataFrame:
    return query_profit_by_brand(client)


@st.cache_data(ttl=300, show_spinner=False)
def load_items_by_category() -> pd.DataFrame:
    return query_items_by_category(client)


@st.cache_data(ttl=300, show_spinner=False)
def load_ingredients(item_name: str | None = None) -> pd.DataFrame:
    return query_ingredients(client, menu_item_name=item_name or None)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filters")

    with st.spinner("Loading filter options…"):
        options = load_filter_options()

    selected_brands: list[str] = st.multiselect(
        "Truck Brand",
        options=options["brands"],
        default=[],
        placeholder="All brands",
    )
    selected_categories: list[str] = st.multiselect(
        "Item Category",
        options=options["categories"],
        default=[],
        placeholder="All categories",
    )
    selected_subcategories: list[str] = st.multiselect(
        "Item Subcategory",
        options=options["subcategories"],
        default=[],
        placeholder="All subcategories",
    )

    st.divider()

    top_n: int = st.selectbox("Leaderboard — Top N", options=[10, 20, 50], index=0)
    sort_by: str = st.radio(
        "Sort leaderboard by",
        options=["profit_usd", "margin_pct"],
        format_func=lambda x: "Profit USD" if x == "profit_usd" else "Margin %",
    )

    st.divider()
    st.success("✅ Snowflake Connected")
    st.caption(f"Schema: `{client.schema}`")

# ---------------------------------------------------------------------------
# Main content — two tabs
# ---------------------------------------------------------------------------
tab_main, tab_ingredients = st.tabs(["📊 Overview", "🥗 Ingredients"])

# ── Tab 1: Overview ─────────────────────────────────────────────────────────
with tab_main:
    with st.spinner("Loading menu data…"):
        raw_df = load_menu(
            brands=tuple(selected_brands),
            categories=tuple(selected_categories),
            subcategories=tuple(selected_subcategories),
        )

    df = clean(raw_df)

    if df.empty:
        st.info("No data for the selected filters. Try removing some constraints.")
        st.stop()

    # ── KPI Row ──────────────────────────────────────────────────────────────
    kpis = calc_kpis(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Menu Items", f"{kpis['item_count']:,}")
    col2.metric("Avg Sale Price", f"${kpis['avg_sale_price']:.2f}")
    col3.metric("Avg Gross Margin", f"{kpis['avg_margin_pct']:.1f}%")

    st.divider()

    # ── Charts ───────────────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Avg Profit Margin % by Truck Brand")
        brand_df = profit_by_group(df, "truck_brand_name")
        if brand_df.empty:
            st.info("No brand data available.")
        else:
            st.bar_chart(
                brand_df.set_index("truck_brand_name")["avg_margin_pct"],
                horizontal=True,
                color="#2563eb",
            )

    with chart_col2:
        st.subheader("Menu Items by Category")
        cat_df = profit_by_group(df, "item_category")
        if cat_df.empty:
            st.info("No category data available.")
        else:
            st.bar_chart(
                cat_df.set_index("item_category")["item_count"],
                horizontal=True,
                color="#16a34a",
            )

    st.divider()

    # ── Leaderboard ───────────────────────────────────────────────────────────
    sort_label = "Profit USD" if sort_by == "profit_usd" else "Margin %"
    st.subheader(f"Top {top_n} Items — sorted by {sort_label}")

    leaderboard = top_items(df, by=sort_by, top_n=top_n)
    display_cols = [
        "menu_item_name",
        "truck_brand_name",
        "item_category",
        "sale_price_usd",
        "cost_of_goods_usd",
        "profit_usd",
        "margin_pct",
    ]
    display_cols = [c for c in display_cols if c in leaderboard.columns]

    st.dataframe(
        leaderboard[display_cols].style.format(
            {
                "sale_price_usd": "${:.2f}",
                "cost_of_goods_usd": "${:.2f}",
                "profit_usd": "${:.2f}",
                "margin_pct": "{:.1f}%",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

# ── Tab 2: Ingredients (LATERAL FLATTEN demo) ────────────────────────────────
with tab_ingredients:
    st.subheader("Ingredients — powered by Snowflake LATERAL FLATTEN")
    st.caption(
        "Ingredients are stored in a VARIANT column (`menu_item_health_metrics_obj`). "
        "This query uses `LATERAL FLATTEN` to expand the nested JSON array into rows."
    )

    item_names: list[str] = (
        sorted(df["menu_item_name"].dropna().unique().tolist()) if not df.empty else []
    )

    selected_item = st.selectbox(
        "Filter by menu item (optional)",
        options=["— Show all —"] + item_names,
        index=0,
    )

    filter_item = None if selected_item == "— Show all —" else selected_item

    with st.spinner("Fetching ingredients via FLATTEN…"):
        ing_df = load_ingredients(filter_item)

    if ing_df.empty:
        st.info("No ingredient data found. The VARIANT column may be NULL for these items.")
    else:
        st.dataframe(ing_df, use_container_width=True, hide_index=True)
        st.caption(f"{len(ing_df):,} ingredient rows returned")
