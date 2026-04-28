"""
BigQuery tracker — records each successful creative animation run.
Only logs final creative videos (not text-only fallbacks or partial files).
"""
import datetime
import uuid

from config import google_cloud, manim as manim_cfg

PROJECT = google_cloud.project_id
DATASET = "mathviz"
TABLE = "animation_runs"
FULL_TABLE = f"{PROJECT}.{DATASET}.{TABLE}"


def _client():
    from google.cloud import bigquery
    return bigquery.Client(project=PROJECT)


_SCHEMA = None  # lazy import to avoid heavy BQ import at module load


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


def ensure_table() -> None:
    """Create the BigQuery dataset and table if they don't already exist."""
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
