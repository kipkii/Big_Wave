from datetime import datetime
import json
import sqlite3
from pathlib import Path

import pandas as pd

from .schema import SCHEMA_SQL


def init_db(db_path: str | Path) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.executescript(SCHEMA_SQL)


def save_analysis_run(
    db_path: str | Path,
    run_metadata: dict,
    raw_df: pd.DataFrame,
    term_daily_df: pd.DataFrame,
    keyword_daily_df: pd.DataFrame,
    ts_result: dict,
    report: dict,
) -> None:
    init_db(db_path)
    run_id = run_metadata["run_id"]

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO analysis_runs
            (run_id, keyword, keyword_set_mode, sources, period_type, start_date, end_date,
             include_related, data_mode, created_at, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                run_metadata["keyword"],
                run_metadata["keyword_set_mode"],
                json.dumps(run_metadata["sources"], ensure_ascii=False),
                run_metadata["period"]["type"],
                run_metadata["period"]["start_date"],
                run_metadata["period"]["end_date"],
                int(run_metadata["include_related"]),
                run_metadata["data_mode"],
                run_metadata["created_at"],
                run_metadata.get("status", "success"),
                run_metadata.get("error_message"),
            ),
        )

        for df, table in (
            (raw_df.assign(run_id=run_id), "raw_items"),
            (term_daily_df.assign(run_id=run_id), "term_daily_metrics"),
            (keyword_daily_df.assign(run_id=run_id), "keyword_set_daily_metrics"),
        ):
            df.to_sql(table, connection, if_exists="append", index=False)

        connection.execute(
            """
            INSERT OR REPLACE INTO analysis_results
            (run_id, ts_score, status_label, growth_score, reaction_score, saturation_score,
             decline_risk, report_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                ts_result["ts_score"],
                ts_result["status_label"],
                ts_result["growth_score"],
                ts_result["reaction_score"],
                ts_result["saturation_score"],
                ts_result["decline_risk"],
                json.dumps(report, ensure_ascii=False),
                datetime.now().isoformat(),
            ),
        )
