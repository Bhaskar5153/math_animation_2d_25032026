"""
BigQuery tracker — records animation runs (successes) and failures.
Failures include: no video produced, pipeline crashes, and Manim render errors.
"""
import datetime
import uuid

from config import google_cloud, manim as manim_cfg

PROJECT = google_cloud.project_id
DATASET = "mathviz"
TABLE = "animation_runs"
FAILURES_TABLE = "animation_failures"
FULL_TABLE = f"{PROJECT}.{DATASET}.{TABLE}"
FULL_FAILURES_TABLE = f"{PROJECT}.{DATASET}.{FAILURES_TABLE}"


def _client():
    from google.cloud import bigquery
    return bigquery.Client(project=PROJECT)


def _get_schema():
    from google.cloud import bigquery
    return [
        bigquery.SchemaField("run_id",            "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("session_id",         "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("question",           "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("solution_filename",  "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("video_filename",     "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("render_quality",     "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("status",             "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("created_at",         "TIMESTAMP", mode="REQUIRED"),
    ]


def _get_failures_schema():
    from google.cloud import bigquery
    return [
        bigquery.SchemaField("failure_id",      "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("session_id",      "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("question",        "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("failure_stage",   "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("error_type",      "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("error_message",   "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("fix_applied",     "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("created_at",      "TIMESTAMP", mode="REQUIRED"),
    ]


def _get_sessions_schema():
    from google.cloud import bigquery
    return [
        bigquery.SchemaField("session_id",       "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("app_name",          "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("user_id",           "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("state_json",        "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("last_update_time",  "FLOAT64",   mode="NULLABLE"),
        bigquery.SchemaField("created_at",        "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("deleted",           "BOOL",      mode="REQUIRED"),
    ]


def _get_events_schema():
    from google.cloud import bigquery
    return [
        bigquery.SchemaField("session_id", "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("event_id",   "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("event_json", "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("timestamp",  "FLOAT64",   mode="REQUIRED"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]


def _get_app_state_schema():
    from google.cloud import bigquery
    return [
        bigquery.SchemaField("app_name",     "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("state_key",    "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("state_value",  "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("last_updated", "FLOAT64",   mode="REQUIRED"),
        bigquery.SchemaField("updated_at",   "TIMESTAMP", mode="REQUIRED"),
    ]


def _get_user_state_schema():
    from google.cloud import bigquery
    return [
        bigquery.SchemaField("app_name",     "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("user_id",      "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("state_key",    "STRING",    mode="REQUIRED"),
        bigquery.SchemaField("state_value",  "STRING",    mode="NULLABLE"),
        bigquery.SchemaField("last_updated", "FLOAT64",   mode="REQUIRED"),
        bigquery.SchemaField("updated_at",   "TIMESTAMP", mode="REQUIRED"),
    ]


def ensure_table() -> None:
    """Create the BigQuery dataset, runs table, and failures table if they don't exist."""
    try:
        from google.cloud import bigquery
        client = _client()

        dataset_ref = bigquery.Dataset(f"{PROJECT}.{DATASET}")
        dataset_ref.location = "US"
        client.create_dataset(dataset_ref, exists_ok=True)
        print(f"[BQ] Dataset ready: {PROJECT}.{DATASET}")

        table = bigquery.Table(FULL_TABLE, schema=_get_schema())
        client.create_table(table, exists_ok=True)
        print(f"[BQ] Table ready: {FULL_TABLE}")

        fail_table = bigquery.Table(FULL_FAILURES_TABLE, schema=_get_failures_schema())
        client.create_table(fail_table, exists_ok=True)
        print(f"[BQ] Table ready: {FULL_FAILURES_TABLE}")

        # ADK session tables
        for tname, schema_fn in [
            ("adk_sessions",   _get_sessions_schema),
            ("adk_events",     _get_events_schema),
            ("adk_app_state",  _get_app_state_schema),
            ("adk_user_state", _get_user_state_schema),
        ]:
            t = bigquery.Table(f"{PROJECT}.{DATASET}.{tname}", schema=schema_fn())
            client.create_table(t, exists_ok=True)
            print(f"[BQ] Table ready: {PROJECT}.{DATASET}.{tname}")

    except Exception as exc:
        print(f"[BQ] Setup warning (non-fatal): {exc}")


def log_run(
    session_id: str,
    question: str,
    solution_filename: str | None,
    video_filename: str | None,
    render_quality: str,
    status: str = "success",
) -> None:
    """
    Insert one row into the animation_runs table.
    Errors are printed but never raised — tracking must not block the pipeline.
    """
    try:
        client = _client()
        rows = [
            {
                "run_id": str(uuid.uuid4()),
                "session_id": session_id,
                "question": question[:2000],
                "solution_filename": solution_filename,
                "video_filename": video_filename,
                "render_quality": render_quality,
                "status": status,
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            }
        ]
        errors = client.insert_rows_json(FULL_TABLE, rows)
        if errors:
            print(f"[BQ] Insert errors: {errors}")
        else:
            print(f"[BQ] Logged session {session_id}: video={video_filename}")
    except Exception as exc:
        print(f"[BQ] log_run failed (non-fatal): {exc}")


def log_failure(
    question: str,
    session_id: str | None = None,
    failure_stage: str | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    fix_applied: str | None = None,
) -> None:
    """
    Insert one row into the animation_failures table.
    Call this whenever a question produces no video or causes a pipeline crash.
    Errors are printed but never raised — tracking must not block the pipeline.
    """
    try:
        client = _client()
        rows = [
            {
                "failure_id":    str(uuid.uuid4()),
                "session_id":    session_id,
                "question":      question[:2000],
                "failure_stage": failure_stage,
                "error_type":    error_type,
                "error_message": error_message[:1000] if error_message else None,
                "fix_applied":   fix_applied,
                "created_at":    datetime.datetime.utcnow().isoformat() + "Z",
            }
        ]
        errors = client.insert_rows_json(FULL_FAILURES_TABLE, rows)
        if errors:
            print(f"[BQ] Failure insert errors: {errors}")
        else:
            print(f"[BQ] Failure logged: stage={failure_stage} q={question[:60]!r}")
    except Exception as exc:
        print(f"[BQ] log_failure failed (non-fatal): {exc}")


def get_failures(limit: int = 50) -> list[dict]:
    """Return the most recent failure records from BigQuery."""
    try:
        client = _client()
        query = f"""
            SELECT
                failure_id, session_id, question,
                failure_stage, error_type, error_message, fix_applied,
                CAST(created_at AS STRING) AS created_at
            FROM `{FULL_FAILURES_TABLE}`
            ORDER BY created_at DESC
            LIMIT {int(limit)}
        """
        return [dict(row) for row in client.query(query).result()]
    except Exception as exc:
        print(f"[BQ] get_failures failed: {exc}")
        return []


def get_history(limit: int = 50) -> list[dict]:
    """Return the most recent animation run records from BigQuery."""
    try:
        client = _client()
        query = f"""
            SELECT
                run_id, session_id, question,
                solution_filename, video_filename,
                render_quality, status,
                CAST(created_at AS STRING) AS created_at
            FROM `{FULL_TABLE}`
            ORDER BY created_at DESC
            LIMIT {int(limit)}
        """
        return [dict(row) for row in client.query(query).result()]
    except Exception as exc:
        print(f"[BQ] get_history failed: {exc}")
        return []
