from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field
from ulid import ULID


class ClusterRecord(BaseModel):
    id: str = Field(..., min_length=1)
    member_ids: list[str] = Field(default_factory=list)
    proposed: bool = False
    proposal_filename: str | None = None
    last_updated: str = Field(..., min_length=1)


class ClusterFile(BaseModel):
    clusters: list[ClusterRecord] = Field(default_factory=list)


def utc_z() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_clusters(path: Path) -> ClusterFile:
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        cf = ClusterFile(clusters=[])
        save_clusters(path, cf)
        return cf
    data = json.loads(path.read_text(encoding="utf-8"))
    return ClusterFile.model_validate(data)


def save_clusters(path: Path, cf: ClusterFile) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cf.model_dump_json(indent=2), encoding="utf-8")


def _merge_closure(
    remaining: list[ClusterRecord], seed_ids: Iterable[str]
) -> tuple[list[ClusterRecord], list[ClusterRecord], set[str]]:
    """Return (untouched_clusters, merged_clusters, merged_member_ids)."""
    pool = set(seed_ids)
    picked: list[ClusterRecord] = []
    while True:
        progressed = False
        new_rem: list[ClusterRecord] = []
        for c in remaining:
            if pool.intersection(set(c.member_ids)):
                pool |= set(c.member_ids)
                picked.append(c)
                progressed = True
            else:
                new_rem.append(c)
        remaining = new_rem
        if not progressed:
            break
    return remaining, picked, pool


def upsert_problem_cluster(
    *,
    clusters_path: Path,
    new_member_id: str,
    related_member_ids: Iterable[str],
) -> tuple[ClusterFile, ClusterRecord]:
    cf = load_clusters(clusters_path)
    remaining, picked, pool = _merge_closure(list(cf.clusters), set(related_member_ids) | {new_member_id})

    cluster_id = f"cl_{ULID()}"
    if picked:
        cluster_id = sorted([c.id for c in picked])[0]

    proposed_any = any(c.proposed for c in picked)
    proposal_fn = next((c.proposal_filename for c in picked if c.proposal_filename), None)

    fresh = ClusterRecord(
        id=cluster_id,
        member_ids=sorted(pool),
        proposed=proposed_any,
        proposal_filename=proposal_fn,
        last_updated=utc_z(),
    )
    cf = ClusterFile(clusters=[*remaining, fresh])
    save_clusters(clusters_path, cf)
    return cf, fresh
