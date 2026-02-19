# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Tasty Bytes Menu Analytics — a Streamlit dashboard backed by live Snowflake data.
Demonstrates VARIANT/FLATTEN queries, clean architecture, pytest coverage, and GitHub Actions CI.

## Commands

```bash
# Run the app (requires .env with Snowflake credentials)
streamlit run app.py

# Run tests (no Snowflake needed)
pytest tests/ -v

# Lint
ruff check .

# Lint + auto-fix
ruff check --fix .
```

## Architecture

```
app.py                      ← Streamlit UI, sidebar filters, KPIs, charts, leaderboard
data/snowflake_client.py    ← SnowflakeClient: connect(), run_query(); reads env vars
data/queries.py             ← 5 query functions (query_all_menu, query_ingredients, …)
processing/transform.py     ← clean(), calc_kpis(), top_items(), profit_by_group()
tests/test_transform.py     ← 12 unit tests for transform.py, no DB required
```

## Snowflake Configuration

All credentials via environment variables (copy `.env.example` → `.env`):

| Variable | Description |
|----------|-------------|
| `SNOWFLAKE_ACCOUNT` | Account identifier (e.g. `abc123.eu-central-1`) |
| `SNOWFLAKE_USER` | Snowflake username |
| `SNOWFLAKE_PASSWORD` | Snowflake password |
| `SNOWFLAKE_ROLE` | `SNOWFLAKE_LEARNING_ROLE` |
| `SNOWFLAKE_WAREHOUSE` | `SNOWFLAKE_LEARNING_WH` |
| `SNOWFLAKE_DATABASE` | `SNOWFLAKE_LEARNING_DB` |
| `SNOWFLAKE_SCHEMA` | `<USERNAME>_LOAD_SAMPLE_DATA_FROM_S3` |

The schema name is username-prefixed; set `SNOWFLAKE_SCHEMA` accordingly.

## Key design decisions

- `@st.cache_resource` for the Snowflake client (one connection per session)
- `@st.cache_data(ttl=300)` for query results (5-min cache, invalidates on filter change)
- Query params passed as tuples to cache functions (lists are not hashable)
- `processing/transform.py` has zero Streamlit or Snowflake imports — fully unit-testable
- `LATERAL FLATTEN` on `menu_item_health_metrics_obj` VARIANT column in `query_ingredients()`
