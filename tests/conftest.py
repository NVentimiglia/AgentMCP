"""Shared fixtures for AgentBridge tests."""

from __future__ import annotations

import hashlib
import math
import random
from pathlib import Path

import pytest

from agent_mcp.cli import cmd_init
from agent_mcp.memory.store import MemoryStore


def deterministic_embed(text: str, dim: int = 384) -> list[float]:
    h = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(h[:8], "big")
    rng = random.Random(seed)
    vec = [rng.uniform(-1.0, 1.0) for _ in range(dim)]
    n = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / n for x in vec]


class _FakeEmbedder:
    def __init__(self, *_, **__) -> None:
        pass

    def embed(self, texts):
        for t in texts:
            yield deterministic_embed(str(t))


@pytest.fixture(autouse=True)
def _reset_runtime_between_tests():
    yield
    from agent_mcp.server import reset_runtime

    reset_runtime()


_TEST_CONFIG = """\
[mode]
rules = "proposal"

[paths]
skills = "skills"
rules_active = "rules/active"
rules_proposals = "rules/proposals"
memory = "memory"

[memory]
backend = "chromadb"
embedding_model = "BAAI/bge-small-en-v1.5"
inject_token_budget = 2000

[problems]
similarity_threshold = 0.05
recurrence_count = 3

[rules]
max_auto_promotions_per_day = 5
"""


@pytest.fixture()
def project_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("AGENT_MCP_ROOT", raising=False)
    monkeypatch.setenv("AGENT_MCP_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    cmd_init(tmp_path)

    (tmp_path / "config.toml").write_text(_TEST_CONFIG, encoding="utf-8")

    monkeypatch.setattr("agent_mcp.memory.store.TextEmbedding", _FakeEmbedder)

    return tmp_path
