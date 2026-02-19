# Snowflake + Streamlit MVP — Tasty Bytes Menu Analytics

[![CI](https://github.com/lesmuc/snowflake-streamlit-mvp/actions/workflows/ci.yml/badge.svg)](https://github.com/lesmuc/snowflake-streamlit-mvp/actions/workflows/ci.yml)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://app-app-mvp-fessbzy7tdavkyb3rtt4uv.streamlit.app/)
![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)
![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?logo=snowflake&logoColor=white)

**Live demo:** [app-app-mvp-fessbzy7tdavkyb3rtt4uv.streamlit.app](https://app-app-mvp-fessbzy7tdavkyb3rtt4uv.streamlit.app/)

A production-quality Streamlit dashboard that queries live Snowflake data from the
**Tasty Bytes** `MENU` table. Built as a portfolio project to demonstrate:

- **Snowflake-native features** — VARIANT columns, `LATERAL FLATTEN` for nested JSON
- **Clean architecture** — separated data, processing, and UI layers
- **Full test coverage** — pytest unit tests, no Snowflake connection required
- **CI/CD** — GitHub Actions with ruff linting + pytest

![Dashboard Screenshot](assets/screenshot.png)

---

## Features

| Feature | Details |
|---------|---------|
| Live Snowflake data | Reads from real `MENU` table, no mock data |
| Sidebar filters | Truck Brand, Item Category, Subcategory, Top-N |
| KPI metrics | Item count, avg sale price, avg gross margin |
| Charts | Profit margin by brand · Items by category |
| Leaderboard | Top-N items sortable by profit or margin |
| Ingredients tab | LATERAL FLATTEN reveals ingredients from VARIANT column |
| Caching | `@st.cache_data` with 5-minute TTL |

---

## Quickstart

### 1. Clone & install

```bash
git clone https://github.com/lesmuc/snowflake-streamlit-mvp.git
cd snowflake-streamlit-mvp
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` and fill in your Snowflake credentials:

```
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_ROLE=SNOWFLAKE_LEARNING_ROLE
SNOWFLAKE_WAREHOUSE=SNOWFLAKE_LEARNING_WH
SNOWFLAKE_DATABASE=SNOWFLAKE_LEARNING_DB
SNOWFLAKE_SCHEMA=YOUR_USERNAME_LOAD_SAMPLE_DATA_FROM_S3
```

### 3. Run

```bash
streamlit run app.py
```

---

## Snowflake Setup

### Required configuration

| Variable | Value |
|----------|-------|
| `SNOWFLAKE_ACCOUNT` | Account identifier from Snowflake URL, e.g. `abc12345.eu-central-1` |
| `SNOWFLAKE_USER` | Your Snowflake username |
| `SNOWFLAKE_PASSWORD` | Your Snowflake password |
| `SNOWFLAKE_ROLE` | `SNOWFLAKE_LEARNING_ROLE` |
| `SNOWFLAKE_WAREHOUSE` | `SNOWFLAKE_LEARNING_WH` |
| `SNOWFLAKE_DATABASE` | `SNOWFLAKE_LEARNING_DB` |
| `SNOWFLAKE_SCHEMA` | `<YOUR_USERNAME>_LOAD_SAMPLE_DATA_FROM_S3` |

### Finding your schema name

The schema name is derived from your Snowflake username. For example, if your username
is `UDO`, the schema is `UDO_LOAD_SAMPLE_DATA_FROM_S3`.

You can verify it in Snowsight:
```sql
SHOW SCHEMAS IN DATABASE SNOWFLAKE_LEARNING_DB;
```

### Loading Tasty Bytes data

Run `setup/load_menu_data.sql` in Snowsight as ACCOUNTADMIN. The script creates the
`MENU` table and inserts 32 sample rows across 8 truck brands — no external S3 access
or additional Snowflake products required.

---

## Project structure

```
snowflake-streamlit-mvp/
├── app.py                      # Streamlit entry point
├── data/
│   ├── snowflake_client.py     # Connection management
│   └── queries.py              # Parametrized SQL (incl. LATERAL FLATTEN)
├── processing/
│   └── transform.py            # clean, calc_kpis, top_items, profit_by_group
├── tests/
│   └── test_transform.py       # 12 pytest unit tests, no Snowflake needed
├── setup/
│   └── load_menu_data.sql      # One-time Snowsight script to create & populate MENU
├── .github/workflows/ci.yml    # Lint + test on every push/PR
├── requirements.txt
├── pyproject.toml              # ruff config
└── .env.example
```

---

## Development

```bash
# Run tests (no Snowflake required)
pytest tests/ -v

# Lint
ruff check .

# Auto-fix lint issues
ruff check --fix .
```

---

## Streamlit Cloud deployment

The app is live at **[app-app-mvp-fessbzy7tdavkyb3rtt4uv.streamlit.app](https://app-app-mvp-fessbzy7tdavkyb3rtt4uv.streamlit.app/)**.

To deploy your own instance:

1. Push this repo to GitHub
2. Create a new app on [share.streamlit.io](https://share.streamlit.io) — point it at `app.py`
3. In the app's **Settings → Secrets**, add your credentials in TOML format:
   ```toml
   SNOWFLAKE_ACCOUNT    = "your_account"
   SNOWFLAKE_USER       = "your_username"
   SNOWFLAKE_PASSWORD   = "your_password"
   SNOWFLAKE_ROLE       = "SNOWFLAKE_LEARNING_ROLE"
   SNOWFLAKE_WAREHOUSE  = "COMPUTE_WH"
   SNOWFLAKE_DATABASE   = "SNOWFLAKE_LEARNING_DB"
   SNOWFLAKE_SCHEMA     = "YOUR_USERNAME_LOAD_SAMPLE_DATA_FROM_S3"
   ```
4. Click **Deploy** — Streamlit installs `requirements.txt` and starts the app
