"""
BigQuery-backed ADK session service for production use.

Stores ADK sessions, events, and state in BigQuery (dataset: mathviz) for
persistence across restarts and across multiple workers.

Table layout:
  adk_sessions  : session_id, app_name, user_id, state_json, last_update_time,
                  created_at, deleted
  adk_events    : session_id, event_id, event_json, timestamp, created_at
  adk_app_state : app_name, state_key, state_value, last_updated, updated_at
  adk_user_state: app_name, user_id, state_key, state_value, last_updated, updated_at

Design notes:
  - BigQuery is append-only; updates are new rows with higher last_update_time.
    Reads use "latest row wins" via ROW_NUMBER() OVER (PARTITION BY … ORDER BY …).
  - Streaming inserts (insert_rows_json) keep write latency low.
  - InMemorySessionService is a write-through cache — BQ is queried only on
    cache misses (post-restart / cross-worker). Active pipeline runs are served
    entirely from in-process memory.
  - Deletes are soft: a tombstone row with deleted=TRUE is appended.
  - All BQ calls are blocking; they run via run_in_executor to avoid blocking
    the asyncio event loop.
"""
from __future__ import annotations

import asyncio
import datetime
import json
import logging
import time as _time
from typing import Any, Optional
from typing_extensions import override

from google.adk.sessions.base_session_service import (
    BaseSessionService,
    GetSessionConfig,
    ListSessionsResponse,
)
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.sessions.session import Session
from google.adk.sessions.state import State
from google.adk.events.event import Event
from google.adk.sessions import _session_util

logger = logging.getLogger("mathviz.bigquery_session")

# Separate logger for memory access events — captured per-job by main.py
# Each record's `msg` is a dict: {"event": str, "detail": str, "ts": float}
memory_logger = logging.getLogger("mathviz.memory")

_SESSIONS_TABLE   = "adk_sessions"
_EVENTS_TABLE     = "adk_events"
_APP_STATE_TABLE  = "adk_app_state"
_USER_STATE_TABLE = "adk_user_state"


class BigQuerySessionService(BaseSessionService):
    """
    Production ADK session service backed by BigQuery.

    Write-through cache (InMemory) serves all same-process reads.
    BigQuery is the durable store used on cache misses and for audit/history.
    """

    def __init__(self, project: str, dataset: str = "mathviz"):
        self._project  = project
        self._dataset  = dataset
        self._cache    = InMemorySessionService()
        self._bq       = None       # lazy BQ client
        self._disabled = False      # set True on unrecoverable BQ errors

    # -----------------------------------------------------------------------
    # BQ client / helper utilities
    # -----------------------------------------------------------------------

    def _client(self):
        if self._bq is None:
            from google.cloud import bigquery
            self._bq = bigquery.Client(project=self._project)
        return self._bq

    def _full_table(self, name: str) -> str:
        """Return the fully-qualified table ref for streaming inserts."""
        return f"{self._project}.{self._dataset}.{name}"

    def _quoted_table(self, name: str) -> str:
        """Return the backtick-quoted table ref for use inside SQL."""
        return f"`{self._project}.{self._dataset}.{name}`"

    def _insert(self, table: str, rows: list[dict]) -> None:
        if self._disabled or not rows:
            return
        try:
            errors = self._client().insert_rows_json(self._full_table(table), rows)
            if errors:
                logger.warning("[BQ Session] Insert errors into %s: %s", table, errors)
        except Exception as exc:
            logger.warning("[BQ Session] insert into %s failed: %s", table, exc)
            if self._is_not_found(exc):
                self._disabled = True

    def _query(self, sql: str, params=None) -> list[dict]:
        if self._disabled:
            return []
        try:
            from google.cloud import bigquery
            cfg = bigquery.QueryJobConfig(query_parameters=params or [])
            return [dict(row) for row in self._client().query(sql, job_config=cfg).result()]
        except Exception as exc:
            logger.warning("[BQ Session] query failed: %s", exc)
            if self._is_not_found(exc):
                self._disabled = True
            return []

    @staticmethod
    def _is_not_found(exc: Exception) -> bool:
        msg = str(exc).lower()
        return "not found" in msg or "does not exist" in msg or "404" in msg

    async def _run(self, fn, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))

    @staticmethod
    def _now_ts() -> float:
        return _time.time()

    @staticmethod
    def _now_iso() -> str:
        return datetime.datetime.utcnow().isoformat() + "Z"

    @staticmethod
    def _encode_state(state: dict[str, Any]) -> str:
        return json.dumps(state)

    @staticmethod
    def _decode_state(state_json: str | None) -> dict[str, Any]:
        if not state_json:
            return {}
        try:
            return json.loads(state_json)
        except Exception:
            return {}

    # -----------------------------------------------------------------------
    # create_session
    # -----------------------------------------------------------------------

    @override
    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        session = await self._cache.create_session(
            app_name=app_name, user_id=user_id, state=state, session_id=session_id
        )
        await self._run(self._bq_create_session, session)
        return session

    def _bq_create_session(self, session: Session) -> None:
        memory_logger.info({
            "event": "SESSION_CREATED",
            "detail": f"New session {session.id[:8]}… persisted to BigQuery",
            "session_id": session.id,
            "ts": self._now_ts(),
        })
        try:
            deltas = _session_util.extract_state_delta(session.state)
            self._insert(_SESSIONS_TABLE, [{
                "session_id":       session.id,
                "app_name":         session.app_name,
                "user_id":          session.user_id,
                "state_json":       self._encode_state(deltas["session"]),
                "last_update_time": session.last_update_time or self._now_ts(),
                "created_at":       self._now_iso(),
                "deleted":          False,
            }])
            if deltas.get("app"):
                self._bq_update_app_state(session.app_name, deltas["app"])
            if deltas.get("user"):
                self._bq_update_user_state(session.app_name, session.user_id, deltas["user"])
        except Exception as exc:
            logger.warning("[BQ Session] create_session persist failed: %s", exc)

    # -----------------------------------------------------------------------
    # get_session
    # -----------------------------------------------------------------------

    @override
    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        cached = await self._cache.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id, config=config
        )
        if cached is not None:
            return cached

        session = await self._run(
            self._bq_load_session, app_name, user_id, session_id, config
        )
        if session is None:
            return None

        # Cache miss — session was loaded from BigQuery (cross-restart persistence)
        event_count = len(session.events) if session.events else 0
        memory_logger.info({
            "event": "SESSION_LOADED_FROM_BQ",
            "detail": (
                f"Session {session_id[:8]}… restored from BigQuery "
                f"({event_count} event{'s' if event_count != 1 else ''} recovered)"
            ),
            "session_id": session_id,
            "event_count": event_count,
            "ts": self._now_ts(),
        })

        try:
            await self._cache.create_session(
                app_name=app_name, user_id=user_id,
                session_id=session_id, state=session.state,
            )
        except Exception:
            pass  # already in cache from a concurrent request

        return session

    def _bq_load_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig],
    ) -> Optional[Session]:
        from google.cloud import bigquery

        rows = self._query(
            f"""
            SELECT session_id, app_name, user_id, state_json, last_update_time
            FROM (
              SELECT *,
                     ROW_NUMBER() OVER (PARTITION BY session_id
                                        ORDER BY last_update_time DESC) AS rn
              FROM {self._quoted_table(_SESSIONS_TABLE)}
              WHERE session_id = @session_id
            )
            WHERE rn = 1 AND NOT deleted
            """,
            params=[bigquery.ScalarQueryParameter("session_id", "STRING", session_id)],
        )
        if not rows:
            return None

        row = rows[0]
        if row.get("app_name") != app_name or row.get("user_id") != user_id:
            return None

        state = self._decode_state(row.get("state_json"))
        events = self._bq_load_events(session_id, config)
        app_state  = self._bq_get_app_state(app_name)
        user_state = self._bq_get_user_state(app_name, user_id)

        for k, v in app_state.items():
            state[State.APP_PREFIX + k] = v
        for k, v in user_state.items():
            state[State.USER_PREFIX + k] = v

        return Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            state=state,
            events=events,
            last_update_time=float(row.get("last_update_time") or 0.0),
        )

    def _bq_load_events(
        self,
        session_id: str,
        config: Optional[GetSessionConfig],
    ) -> list[Event]:
        from google.cloud import bigquery

        params = [bigquery.ScalarQueryParameter("session_id", "STRING", session_id)]
        extra_where = ""
        order = "ORDER BY timestamp ASC"
        limit = ""

        if config and config.after_timestamp:
            extra_where = "AND timestamp > @after_ts"
            params.append(bigquery.ScalarQueryParameter(
                "after_ts", "FLOAT64", config.after_timestamp
            ))
        if config and config.num_recent_events:
            order = "ORDER BY timestamp DESC"
            limit = f"LIMIT {int(config.num_recent_events)}"

        rows = self._query(
            f"""
            SELECT event_json
            FROM {self._quoted_table(_EVENTS_TABLE)}
            WHERE session_id = @session_id {extra_where}
            {order} {limit}
            """,
            params=params,
        )
        if config and config.num_recent_events:
            rows = list(reversed(rows))

        events: list[Event] = []
        for r in rows:
            try:
                events.append(Event.model_validate_json(r["event_json"]))
            except Exception as e:
                logger.warning("[BQ Session] Could not deserialize event: %s", e)
        return events

    # -----------------------------------------------------------------------
    # list_sessions
    # -----------------------------------------------------------------------

    @override
    async def list_sessions(
        self, *, app_name: str, user_id: Optional[str] = None
    ) -> ListSessionsResponse:
        sessions = await self._run(self._bq_list_sessions, app_name, user_id)
        return ListSessionsResponse(sessions=sessions)

    def _bq_list_sessions(
        self, app_name: str, user_id: Optional[str]
    ) -> list[Session]:
        from google.cloud import bigquery

        params = [bigquery.ScalarQueryParameter("app_name", "STRING", app_name)]
        user_clause = ""
        if user_id:
            user_clause = "AND user_id = @user_id"
            params.append(bigquery.ScalarQueryParameter("user_id", "STRING", user_id))

        rows = self._query(
            f"""
            SELECT session_id, app_name, user_id, state_json, last_update_time
            FROM (
              SELECT *,
                     ROW_NUMBER() OVER (PARTITION BY session_id
                                        ORDER BY last_update_time DESC) AS rn
              FROM {self._quoted_table(_SESSIONS_TABLE)}
              WHERE app_name = @app_name {user_clause}
            )
            WHERE rn = 1 AND NOT deleted
            ORDER BY last_update_time DESC
            LIMIT 200
            """,
            params=params,
        )
        return [
            Session(
                id=r["session_id"],
                app_name=r["app_name"],
                user_id=r["user_id"],
                state=self._decode_state(r.get("state_json")),
                last_update_time=float(r.get("last_update_time") or 0.0),
            )
            for r in rows
        ]

    # -----------------------------------------------------------------------
    # delete_session
    # -----------------------------------------------------------------------

    @override
    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        await self._cache.delete_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )
        await self._run(self._bq_delete_session, app_name, user_id, session_id)

    def _bq_delete_session(
        self, app_name: str, user_id: str, session_id: str
    ) -> None:
        # Tombstone row — latest last_update_time + deleted=True wins in queries
        self._insert(_SESSIONS_TABLE, [{
            "session_id":       session_id,
            "app_name":         app_name,
            "user_id":          user_id,
            "state_json":       "{}",
            "last_update_time": self._now_ts(),
            "created_at":       self._now_iso(),
            "deleted":          True,
        }])

    # -----------------------------------------------------------------------
    # append_event  (hot path — called every ADK agent turn)
    # -----------------------------------------------------------------------

    @override
    async def append_event(self, session: Session, event: Event) -> Event:
        if event.partial:
            return event

        event = await self._cache.append_event(session=session, event=event)

        event_json  = event.model_dump_json()
        state_deltas: dict = {}
        if event.actions and event.actions.state_delta:
            state_deltas = _session_util.extract_state_delta(event.actions.state_delta)

        session_state_only = {
            k: v for k, v in session.state.items()
            if not k.startswith(State.APP_PREFIX)
            and not k.startswith(State.USER_PREFIX)
        }

        await self._run(
            self._bq_persist_event,
            session.app_name, session.user_id, session.id,
            event.id, event_json, event.timestamp,
            session_state_only, state_deltas,
        )
        return event

    def _bq_persist_event(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        event_id: str,
        event_json: str,
        timestamp: float,
        session_state: dict,
        state_deltas: dict,
    ) -> None:
        now_ts  = self._now_ts()
        now_iso = self._now_iso()

        state_keys = list(session_state.keys()) if session_state else []
        memory_logger.info({
            "event": "EVENT_SAVED_TO_BQ",
            "detail": (
                f"Agent turn persisted to BigQuery "
                f"(state keys: {', '.join(state_keys) if state_keys else 'none'})"
            ),
            "session_id": session_id,
            "event_id": event_id[:8] + "…",
            "state_keys": state_keys,
            "ts": now_ts,
        })

        self._insert(_EVENTS_TABLE, [{
            "session_id": session_id,
            "event_id":   event_id,
            "event_json": event_json,
            "timestamp":  timestamp,
            "created_at": now_iso,
        }])

        self._insert(_SESSIONS_TABLE, [{
            "session_id":       session_id,
            "app_name":         app_name,
            "user_id":          user_id,
            "state_json":       self._encode_state(session_state),
            "last_update_time": now_ts,
            "created_at":       now_iso,
            "deleted":          False,
        }])

        if state_deltas.get("app"):
            self._bq_update_app_state(app_name, state_deltas["app"])
        if state_deltas.get("user"):
            self._bq_update_user_state(app_name, user_id, state_deltas["user"])

    # -----------------------------------------------------------------------
    # App / User state helpers
    # -----------------------------------------------------------------------

    def _bq_update_app_state(self, app_name: str, delta: dict[str, Any]) -> None:
        now_ts  = self._now_ts()
        now_iso = self._now_iso()
        self._insert(_APP_STATE_TABLE, [
            {
                "app_name":     app_name,
                "state_key":    k,
                "state_value":  json.dumps(v),
                "last_updated": now_ts,
                "updated_at":   now_iso,
            }
            for k, v in delta.items()
        ])

    def _bq_update_user_state(
        self, app_name: str, user_id: str, delta: dict[str, Any]
    ) -> None:
        now_ts  = self._now_ts()
        now_iso = self._now_iso()
        self._insert(_USER_STATE_TABLE, [
            {
                "app_name":     app_name,
                "user_id":      user_id,
                "state_key":    k,
                "state_value":  json.dumps(v),
                "last_updated": now_ts,
                "updated_at":   now_iso,
            }
            for k, v in delta.items()
        ])

    def _bq_get_app_state(self, app_name: str) -> dict[str, Any]:
        from google.cloud import bigquery

        rows = self._query(
            f"""
            SELECT state_key, state_value
            FROM (
              SELECT state_key, state_value,
                     ROW_NUMBER() OVER (PARTITION BY state_key
                                        ORDER BY last_updated DESC) AS rn
              FROM {self._quoted_table(_APP_STATE_TABLE)}
              WHERE app_name = @app_name
            )
            WHERE rn = 1
            """,
            params=[bigquery.ScalarQueryParameter("app_name", "STRING", app_name)],
        )
        return self._decode_state_rows(rows)

    def _bq_get_user_state(self, app_name: str, user_id: str) -> dict[str, Any]:
        from google.cloud import bigquery

        rows = self._query(
            f"""
            SELECT state_key, state_value
            FROM (
              SELECT state_key, state_value,
                     ROW_NUMBER() OVER (PARTITION BY state_key
                                        ORDER BY last_updated DESC) AS rn
              FROM {self._quoted_table(_USER_STATE_TABLE)}
              WHERE app_name = @app_name AND user_id = @user_id
            )
            WHERE rn = 1
            """,
            params=[
                bigquery.ScalarQueryParameter("app_name", "STRING", app_name),
                bigquery.ScalarQueryParameter("user_id",  "STRING", user_id),
            ],
        )
        return self._decode_state_rows(rows)

    @staticmethod
    def _decode_state_rows(rows: list[dict]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for r in rows:
            v = r.get("state_value")
            try:
                result[r["state_key"]] = json.loads(v) if isinstance(v, str) else v
            except Exception:
                result[r["state_key"]] = v
        return result
