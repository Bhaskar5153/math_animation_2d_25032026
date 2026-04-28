"""
Firestore-backed ADK session service.

Stores ADK sessions, events, and shared state in Cloud Firestore for
production-grade persistence — survives server restarts and works correctly
across multiple process workers.

Firestore collection layout:
  adk_sessions/{session_id}
      fields: app_name, user_id, state (map), last_update_time, created_at

  adk_sessions/{session_id}/events/{event_id}
      fields: event_json (str), timestamp (float)

  adk_app_state/{app_name}
      fields: state (map of key → JSON-encoded value string)

  adk_user_state/{app_name}__{user_id}
      fields: state (map of key → JSON-encoded value string)

Design:
  - InMemorySessionService is used as a write-through cache: all reads within
    the same process hit memory first (no Firestore round-trip per agent turn).
  - Firestore is the canonical store: on cache miss the session is reconstructed
    from Firestore and the cache is warmed (cross-process / post-restart).
  - All blocking Firestore calls run via run_in_executor so the asyncio event
    loop is never blocked.
  - State values are JSON-encoded strings for type-safety across all contexts.
"""
from __future__ import annotations

import asyncio
import concurrent.futures
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

logger = logging.getLogger("mathviz.firestore_session")


class FirestoreSessionService(BaseSessionService):
    """
    Production ADK session service backed by Cloud Firestore.

    Uses an in-process InMemorySessionService as a write-through cache so
    reads within the same pipeline run are instant. Firestore is the source of
    truth that persists across restarts and is shared across workers.
    """

    def __init__(self, project: str):
        self._project = project
        self._cache = InMemorySessionService()
        self._db = None        # lazy Firestore client
        self._fs_disabled = False  # set True on unrecoverable Firestore errors

    # ------------------------------------------------------------------
    # Client helpers
    # ------------------------------------------------------------------

    FIRESTORE_DATABASE = "mathviz-memory"

    def _client(self):
        if self._db is None:
            from google.cloud import firestore
            self._db = firestore.Client(
                project=self._project,
                database=self.FIRESTORE_DATABASE,
            )
        return self._db

    def _is_db_missing(self, exc: Exception) -> bool:
        """Return True for the 404 'database does not exist' error."""
        msg = str(exc)
        return "404" in msg and ("does not exist" in msg or "datastore" in msg.lower())

    def _sessions_col(self):
        return self._client().collection("adk_sessions")

    def _session_doc(self, session_id: str):
        return self._sessions_col().document(session_id)

    def _events_col(self, session_id: str):
        return self._session_doc(session_id).collection("events")

    def _app_state_doc(self, app_name: str):
        return self._client().collection("adk_app_state").document(app_name)

    def _user_state_doc(self, app_name: str, user_id: str):
        # double-underscore separator — both are controlled ASCII strings
        return self._client().collection("adk_user_state").document(
            f"{app_name}__{user_id}"
        )

    async def _run(self, fn, *args, **kwargs):
        """Run a blocking Firestore call in the default thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: fn(*args, **kwargs))

    # ------------------------------------------------------------------
    # create_session
    # ------------------------------------------------------------------

    @override
    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        # In-memory cache handles duplicate-session detection
        session = await self._cache.create_session(
            app_name=app_name, user_id=user_id, state=state, session_id=session_id,
        )
        await self._run(self._fs_create_session, session)
        return session

    def _fs_create_session(self, session: Session) -> None:
        if self._fs_disabled:
            return
        try:
            from google.cloud import firestore as _fs
            deltas = _session_util.extract_state_delta(session.state)

            self._session_doc(session.id).set({
                "session_id":       session.id,
                "app_name":         session.app_name,
                "user_id":          session.user_id,
                "state":            self._encode_state(deltas["session"]),
                "last_update_time": session.last_update_time,
                "created_at":       _fs.SERVER_TIMESTAMP,
            })

            # Persist initial app / user state if provided
            if deltas["app"]:
                self._fs_update_app_state(session.app_name, deltas["app"])
            if deltas["user"]:
                self._fs_update_user_state(session.app_name, session.user_id, deltas["user"])
        except Exception as exc:
            if self._is_db_missing(exc):
                self._fs_disabled = True
                logger.warning(
                    "[Firestore Session] Database does not exist — falling back to in-memory "
                    "sessions. Create it at: https://console.cloud.google.com/datastore/setup"
                    f"?project={self._project}"
                )
            else:
                logger.warning(f"[Firestore Session] create_session persist failed: {exc}")

    # ------------------------------------------------------------------
    # get_session
    # ------------------------------------------------------------------

    @override
    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        # Fast path: in-memory cache (same process, same run)
        cached = await self._cache.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id, config=config,
        )
        if cached is not None:
            return cached

        # Cache miss: reconstruct from Firestore (post-restart / cross-process)
        session = await self._run(
            self._fs_load_session, app_name, user_id, session_id, config
        )
        if session is None:
            return None

        # Warm the cache for subsequent reads in this process
        try:
            await self._cache.create_session(
                app_name=app_name, user_id=user_id,
                session_id=session_id, state=session.state,
            )
        except Exception:
            pass  # already cached from a concurrent request — safe to ignore

        return session

    def _fs_load_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig],
    ) -> Optional[Session]:
        if self._fs_disabled:
            return None
        try:
            snap = self._session_doc(session_id).get()
            if not snap.exists:
                return None

            data = snap.to_dict()
            if data.get("app_name") != app_name or data.get("user_id") != user_id:
                return None

            state = self._decode_state(data.get("state") or {})

            # Fan out events + app_state + user_state reads in parallel
            def _fetch_events() -> list[Event]:
                q = self._events_col(session_id).order_by("timestamp")
                if config and config.after_timestamp:
                    q = q.where("timestamp", ">", config.after_timestamp)
                if config and config.num_recent_events:
                    q = q.order_by("timestamp", direction="DESCENDING").limit(
                        config.num_recent_events
                    )
                snaps = list(q.stream())
                if config and config.num_recent_events:
                    snaps = list(reversed(snaps))
                evts: list[Event] = []
                for es in snaps:
                    try:
                        evts.append(Event.model_validate_json(es.to_dict()["event_json"]))
                    except Exception as e:
                        logger.warning(f"[Firestore Session] Could not deserialize event: {e}")
                return evts

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                f_events = pool.submit(_fetch_events)
                f_app    = pool.submit(self._fs_get_app_state, app_name)
                f_user   = pool.submit(self._fs_get_user_state, app_name, user_id)
                events     = f_events.result()
                app_state  = f_app.result()
                user_state = f_user.result()

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
                last_update_time=data.get("last_update_time", 0.0),
            )
        except Exception as exc:
            if self._is_db_missing(exc):
                self._fs_disabled = True
                logger.warning(
                    "[Firestore Session] Database does not exist — falling back to in-memory sessions."
                )
            else:
                logger.warning(f"[Firestore Session] load_session failed: {exc}")
            return None

    # ------------------------------------------------------------------
    # list_sessions
    # ------------------------------------------------------------------

    @override
    async def list_sessions(
        self, *, app_name: str, user_id: Optional[str] = None
    ) -> ListSessionsResponse:
        sessions = await self._run(self._fs_list_sessions, app_name, user_id)
        return ListSessionsResponse(sessions=sessions)

    def _fs_list_sessions(
        self, app_name: str, user_id: Optional[str]
    ) -> list[Session]:
        if self._fs_disabled:
            return []
        try:
            query = self._sessions_col().where("app_name", "==", app_name)
            if user_id:
                query = query.where("user_id", "==", user_id)
            query = query.order_by("last_update_time", direction="DESCENDING").limit(200)

            sessions = []
            for snap in query.stream():
                d = snap.to_dict()
                sessions.append(Session(
                    id=d["session_id"],
                    app_name=d["app_name"],
                    user_id=d["user_id"],
                    state=self._decode_state(d.get("state") or {}),
                    last_update_time=d.get("last_update_time", 0.0),
                ))
            return sessions
        except Exception as exc:
            logger.warning(f"[Firestore Session] list_sessions failed: {exc}")
            return []

    # ------------------------------------------------------------------
    # delete_session
    # ------------------------------------------------------------------

    @override
    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        await self._cache.delete_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )
        await self._run(self._fs_delete_session, session_id)

    def _fs_delete_session(self, session_id: str) -> None:
        if self._fs_disabled:
            return
        try:
            # Delete all events in the subcollection first
            for snap in self._events_col(session_id).stream():
                snap.reference.delete()
            # Delete the session document
            self._session_doc(session_id).delete()
        except Exception as exc:
            logger.warning(f"[Firestore Session] delete_session failed: {exc}")

    # ------------------------------------------------------------------
    # append_event — hot path (called on every ADK agent turn)
    # ------------------------------------------------------------------

    @override
    async def append_event(self, session: Session, event: Event) -> Event:
        if event.partial:
            return event

        # Update in-memory cache (handles temp state, state delta merge, etc.)
        event = await self._cache.append_event(session=session, event=event)

        event_json = event.model_dump_json()

        # State delta from this event
        state_deltas: dict = {}
        if event.actions and event.actions.state_delta:
            state_deltas = _session_util.extract_state_delta(event.actions.state_delta)

        # Session-scoped state only (strip app: / user: prefixes before storing)
        session_state_only = {
            k: v for k, v in session.state.items()
            if not k.startswith(State.APP_PREFIX)
            and not k.startswith(State.USER_PREFIX)
        }

        await self._run(
            self._fs_persist_event,
            session.app_name, session.user_id, session.id,
            event.id, event_json, event.timestamp,
            session_state_only, state_deltas,
        )
        return event

    def _fs_persist_event(
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
        if self._fs_disabled:
            return
        try:
            now = _time.time()

            def _write_event() -> None:
                self._events_col(session_id).document(event_id).set({
                    "event_json": event_json,
                    "timestamp":  timestamp,
                })

            def _update_session() -> None:
                self._session_doc(session_id).update({
                    "state":            self._encode_state(session_state),
                    "last_update_time": now,
                })

            def _update_app() -> None:
                if state_deltas.get("app"):
                    self._fs_update_app_state(app_name, state_deltas["app"])

            def _update_user() -> None:
                if state_deltas.get("user"):
                    self._fs_update_user_state(app_name, user_id, state_deltas["user"])

            # All 4 writes target different Firestore documents — safe to parallelise
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = [
                    pool.submit(_write_event),
                    pool.submit(_update_session),
                    pool.submit(_update_app),
                    pool.submit(_update_user),
                ]
                for f in concurrent.futures.as_completed(futures):
                    f.result()  # re-raise any write errors into the outer except

        except Exception as exc:
            if self._is_db_missing(exc):
                self._fs_disabled = True
                logger.warning(
                    "[Firestore Session] Database does not exist — falling back to in-memory sessions."
                )
            else:
                logger.warning(f"[Firestore Session] persist_event failed (non-fatal): {exc}")

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    def _fs_update_app_state(self, app_name: str, delta: dict[str, Any]) -> None:
        """Upsert key-value pairs into the app state document."""
        try:
            doc = self._app_state_doc(app_name)
            # Use dot-notation updates so only the changed keys are touched
            updates = {f"state.{k}": json.dumps(v) for k, v in delta.items()}
            doc.set({"state": {}}, merge=True)  # ensure doc exists
            doc.update(updates)
        except Exception as exc:
            logger.warning(f"[Firestore Session] update_app_state failed: {exc}")

    def _fs_update_user_state(
        self, app_name: str, user_id: str, delta: dict[str, Any]
    ) -> None:
        """Upsert key-value pairs into the user state document."""
        try:
            doc = self._user_state_doc(app_name, user_id)
            updates = {f"state.{k}": json.dumps(v) for k, v in delta.items()}
            doc.set({"state": {}}, merge=True)  # ensure doc exists
            doc.update(updates)
        except Exception as exc:
            logger.warning(f"[Firestore Session] update_user_state failed: {exc}")

    def _fs_get_app_state(self, app_name: str) -> dict[str, Any]:
        try:
            snap = self._app_state_doc(app_name).get()
            if not snap.exists:
                return {}
            return self._decode_state(snap.to_dict().get("state") or {})
        except Exception as exc:
            logger.warning(f"[Firestore Session] get_app_state failed: {exc}")
            return {}

    def _fs_get_user_state(self, app_name: str, user_id: str) -> dict[str, Any]:
        try:
            snap = self._user_state_doc(app_name, user_id).get()
            if not snap.exists:
                return {}
            return self._decode_state(snap.to_dict().get("state") or {})
        except Exception as exc:
            logger.warning(f"[Firestore Session] get_user_state failed: {exc}")
            return {}

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _encode_state(state: dict[str, Any]) -> dict[str, str]:
        """JSON-encode each state value so Firestore stores it as a plain string."""
        return {k: json.dumps(v) for k, v in state.items()}

    @staticmethod
    def _decode_state(encoded: dict[str, str]) -> dict[str, Any]:
        """Decode JSON-encoded state values back to Python objects."""
        result = {}
        for k, v in encoded.items():
            try:
                result[k] = json.loads(v) if isinstance(v, str) else v
            except Exception:
                result[k] = v
        return result
