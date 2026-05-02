from __future__ import annotations

import json
from datetime import UTC, datetime



from agent_mcp.memory.store import MemoryStore
from agent_mcp.server import configure_for_tests, memory_search, memory_store, memory_reinforce


def _store(project_home) -> MemoryStore:
    configure_for_tests(project_home)
    return MemoryStore.from_app()


def test_memory_roundtrip_via_mcp_helpers(project_home) -> None:
    configure_for_tests(project_home)
    out = json.loads(memory_store("hello world corpus alpha", tags=["pattern"], source="tests"))
    assert out["tags"] == ["pattern"]
    hits = json.loads(memory_search("alpha hello", k=5))
    assert hits and hits[0]["text"]


def test_reinforce_bumps_counters(project_home) -> None:
    store = _store(project_home)
    row = store.add_entry(text="reinforcement-only", tags=["note"], source="tests")
    store.reinforce([row["id"]])
    store.reinforce([row["id"]])
    _row2 = json.loads(memory_reinforce([row["id"]]))
    assert _row2["ok"]


def test_prune_drops_old_unreinforced(project_home, monkeypatch) -> None:
    """New entries idle >30 days are deleted; reinforced entries are skipped."""
    import agent_mcp.memory.store as ms

    t0 = datetime(2026, 5, 2, tzinfo=UTC)

    monkeypatch.setattr(ms, "utcnow_iso", lambda: "2026-01-01T00:00:00Z")
    monkeypatch.setattr(ms, "_utc_now", lambda: t0)

    store = _store(project_home)
    store.add_entry(text="stale", tags=["note"], source="tests")
    assert store.prune() == 1

    monkeypatch.setattr(
        ms,
        "utcnow_iso",
        lambda: datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    monkeypatch.setattr(ms, "_utc_now", lambda: datetime.now(UTC))

    keep = store.add_entry(text="keep-new", tags=["note"], source="tests")
    store.reinforce([keep["id"]])

    monkeypatch.setattr(ms, "utcnow_iso", lambda: "2026-01-01T00:00:00Z")
    monkeypatch.setattr(ms, "_utc_now", lambda: t0)
    assert store.prune() == 0


def test_hybrid_prefers_shared_tokens(project_home) -> None:
    store = _store(project_home)
    store.add_entry(text="foo bar zed unique1", tags=["pattern"], source="t")
    store.add_entry(text="foo bar qux unique2", tags=["pattern"], source="t")
    store.add_entry(text="something else entirely", tags=["pattern"], source="t")
    ranked = store.hybrid_search("foo bar qux", k=2)
    assert ranked[0][1]["text"].startswith("foo bar qux")
