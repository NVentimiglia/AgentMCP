from __future__ import annotations

from typing import Any

from agent_mcp.app_state import get_app
from agent_mcp.clusters import ClusterFile, save_clusters, utc_z, upsert_problem_cluster
from agent_mcp.memory.store import MemoryStore
from agent_mcp.rules.service import RulesService


def handle_flag_problem(
    *,
    description: str,
    context: str,
    memory: MemoryStore,
    rules_svc: RulesService,
    source_session_id: str,
) -> dict[str, Any]:
    app = get_app()
    query = description if not context.strip() else f"{description}\n\n{context}".strip()

    new_row = memory.add_entry(text=query, tags=["problem"], source="flag_problem")
    new_id = str(new_row["id"])

    thr = float(app.config.problems.similarity_threshold)
    need = int(app.config.problems.recurrence_count)

    prior = memory.problem_matches_at_or_above_threshold(query=query, threshold=thr, exclude_id=new_id)
    prior_ids = [str(row["id"]) for _sc, row in prior]

    cf, cluster = upsert_problem_cluster(
        clusters_path=app.clusters_path,
        new_member_id=new_id,
        related_member_ids=prior_ids,
    )

    recurrence_hit = len(cluster.member_ids) >= need

    proposal_info: dict[str, Any] = {}
    if recurrence_hit and (not cluster.proposed):
        trigger = (
            f"Repeated problem recurrence ({len(cluster.member_ids)} similar reports): "
            f"{description[:500]}"
        )
        solution = (
            "Automatically proposed from recurring `flag_problem` reports. Review member IDs: "
            + ", ".join(cluster.member_ids[:50])
            + ("…" if len(cluster.member_ids) > 50 else "")
        )

        proposal_info = rules_svc.propose_rule_md(
            trigger=trigger,
            solution=solution,
            source_session_id=source_session_id,
        )

        filename = None
        pth = str(proposal_info.get("path") or "")
        if pth.startswith("rules/proposals/"):
            filename = pth.split("/", 2)[-1]
        elif pth.startswith("rules/active/"):
            filename = pth.split("/", 2)[-1]

        now = utc_z()
        replaced = []
        for c in cf.clusters:
            if c.id == cluster.id:
                replaced.append(
                    c.model_copy(
                        update={
                            "proposed": True,
                            "proposal_filename": filename or c.proposal_filename,
                            "last_updated": now,
                        }
                    )
                )
            else:
                replaced.append(c)
        save_clusters(app.clusters_path, ClusterFile(clusters=replaced))
        cluster = next(c for c in replaced if c.id == cluster.id)

    return {
        "memory": new_row,
        "cluster": cluster.model_dump(),
        "recurrence_hit": recurrence_hit,
        "proposal": proposal_info,
    }
