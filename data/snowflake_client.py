"""Snowflake connection management and query execution."""

from __future__ import annotations

import os

import pandas as pd  # noqa: I001
import streamlit as st

_REQUIRED_ENV_VARS = [
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_PASSWORD",
    "SNOWFLAKE_ROLE",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_DATABASE",
    "SNOWFLAKE_SCHEMA",
]


def _check_env_vars() -> None:
    missing = [v for v in _REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        raise OSError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in your credentials."
        )


class SnowflakeClient:
    """Thin wrapper around snowflake-connector-python for Streamlit apps.

    Reads all credentials from environment variables so the same code works
    both locally (via .env / dotenv) and on Streamlit Cloud (via secrets).
    """

    def __init__(self) -> None:
        _check_env_vars()
        self._account = os.environ["SNOWFLAKE_ACCOUNT"]
        self._user = os.environ["SNOWFLAKE_USER"]
        self._password = os.environ["SNOWFLAKE_PASSWORD"]
        self._role = os.environ["SNOWFLAKE_ROLE"]
        self._warehouse = os.environ["SNOWFLAKE_WAREHOUSE"]
        self._database = os.environ["SNOWFLAKE_DATABASE"]
        self._schema = os.environ["SNOWFLAKE_SCHEMA"]
        self._conn = None

    def connect(self) -> None:
        """Open a Snowflake connection. Calls st.stop() on failure."""
        try:
            import snowflake.connector  # noqa: PLC0415

            self._conn = snowflake.connector.connect(
                account=self._account,
                user=self._user,
                password=self._password,
                role=self._role,
                warehouse=self._warehouse,
                database=self._database,
                schema=self._schema,
            )
        except Exception as exc:
            st.error(
                f"**Snowflake connection failed:** {exc}\n\n"
                "Check that all `SNOWFLAKE_*` environment variables are set correctly "
                "and that your account identifier, credentials, and network are valid."
            )
            st.stop()

    def run_query(self, sql: str, params: dict | None = None) -> pd.DataFrame:
        """Execute *sql* with optional *params* and return a DataFrame.

        Parameters use ``%(key)s`` placeholders compatible with the Snowflake
        connector's DictCursor.
        """
        if self._conn is None:
            self.connect()

        try:
            with self._conn.cursor() as cur:  # type: ignore[attr-defined]
                cur.execute(sql, params or {})
                columns = [desc[0].lower() for desc in cur.description]
                rows = cur.fetchall()
            return pd.DataFrame(rows, columns=columns)
        except Exception as exc:
            schema_hint = (
                " Hint: verify that `SNOWFLAKE_SCHEMA` matches your actual schema name "
                "(e.g. UDO_LOAD_SAMPLE_DATA_FROM_S3)."
                if "does not exist" in str(exc).lower() or "unknown" in str(exc).lower()
                else ""
            )
            st.error(f"**Query failed:** {exc}{schema_hint}")
            st.stop()

    @property
    def schema(self) -> str:
        return self._schema

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
