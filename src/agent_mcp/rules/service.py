from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml
from ulid import ULID

from agent_mcp.app_state import AppContext
from agent_mcp.rules.loader import ActiveRuleIndex
from agent_mcp.rules.schema import RuleFrontmatter


def _b64_utf8(txt: str) -> str:
    return base64.b64encode(txt.encode("utf-8")).decode("ascii")


def _b64_utf8_optional(txt: str | None) -> str | None:
    if txt is None:
        return None
    return _b64_utf8(txt)


def _dec_b64_optional(s: str | None) -> str | None:
    if s is None:
        return None
    raw = base64.b64decode(s.encode("ascii"))
    return raw.decode("utf-8")


def utc_today_iso() -> str:
    return datetime.now(UTC).date().isoformat()


@dataclass
class PromotionCounter:
    day: str
    count: int

    @staticmethod
    def load(path: Path) -> PromotionCounter:
        if not path.is_file():
            return PromotionCounter(day=utc_today_iso(), count=0)
        data = json.loads(path.read_text(encoding="utf-8"))
        day = str(data.get("day") or utc_today_iso())
        count = int(data.get("count") or 0)
        today = utc_today_iso()
        if day != today:
            return PromotionCounter(day=today, count=0)
        return PromotionCounter(day=today, count=count)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"day": self.day, "count": self.count}), encoding="utf-8")


class RulesJournal:
    def __init__(self, machine_log: Path, human_md: Path) -> None:
        self.machine_log = machine_log
        self.human_md = human_md

    def append(self, entry: dict[str, Any], human_lines: list[str]) -> dict[str, Any]:
        self.machine_log.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, separators=(",", ":"), sort_keys=False)
        with self.machine_log.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        self.human_md.parent.mkdir(parents=True, exist_ok=True)
        if human_lines:
            blob = "\n".join(human_lines).rstrip() + "\n\n"
            with self.human_md.open("a", encoding="utf-8") as hm:
                hm.write(blob)
        return entry


class RulesService:
    MACHINE_LOG_NAME = "machine_changelog.jsonl"

    def __init__(self, app: AppContext, active_index: ActiveRuleIndex | None = None) -> None:
        self.app = app
        self.rules_root = (app.root / "rules").resolve()
        self.active_dir = app.rules_active_dir
        self.proposals_dir = app.rules_proposals_dir
        self.human_md = app.changelog_path
        self.machine_log = self.rules_root / self.MACHINE_LOG_NAME
        self.journal = RulesJournal(machine_log=self.machine_log, human_md=self.human_md)
        self.promo_counter_path = app.state_dir / "auto_promotions.json"
        self._index = active_index

    def _index_reload(self) -> None:
        if self._index is None:
            return
        self._index.reload()

    def propose_rule_md(
        self,
        *,
        trigger: str,
        solution: str,
        source_session_id: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).date().isoformat()
        rid = str(ULID())

        fm = RuleFrontmatter(
            id=rid,
            version=now,
            trigger=trigger,
            solution=solution,
        )
        dump = yaml.safe_dump(fm.model_dump(), sort_keys=False, allow_unicode=True).strip()
        body_txt = ""
        md = f"---\n{dump}\n---\n{body_txt}\n"

        from agent_mcp.security import slugify_trigger

        slug = slugify_trigger(trigger)
        filename = f"{now}-{slug}.md".replace(":", "-")

        cfg = self.app.config
        if cfg.mode.rules == "proposal":
            out = self._write_proposals_only(md, filename, source_session_id=source_session_id)
            return out

        # auto mode attempts active path with cap
        promo = PromotionCounter.load(self.promo_counter_path)
        promo_today_ok = promo.count < int(cfg.rules.max_auto_promotions_per_day)

        if promo_today_ok:
            target_active = filename
            rel_active = Path("active") / target_active
            before = None
            self.active_dir.mkdir(parents=True, exist_ok=True)
            active_path = self.active_dir / target_active
            if active_path.exists():
                before = active_path.read_text(encoding="utf-8")

            active_path.write_text(md, encoding="utf-8")

            promo.count += 1
            promo.day = utc_today_iso()
            promo.save(self.promo_counter_path)

            entry_id = str(ULID())
            snapshot = [
                {
                    "rel": str(rel_active).replace("\\", "/"),
                    "before_b64": _b64_utf8_optional(before),
                    "after_b64": _b64_utf8(md),
                }
            ]
            entry = {
                "id": entry_id,
                "op": "AUTO_PROPOSE_ACTIVE",
                "source_session_id": source_session_id,
                "snapshot": snapshot,
            }
            self.journal.append(
                entry,
                human_lines=[
                    f"### {entry_id} AUTO_PROPOSE_ACTIVE",
                    f"- source_session: `{source_session_id}`",
                    f"- wrote `rules/active/{target_active}`",
                ],
            )
            self._index_reload()
            return {"mode": "auto", "path": f"rules/active/{target_active}", "changelog_id": entry_id}

        out = self._write_proposals_only(md, filename, source_session_id=source_session_id, reason="daily_cap")
        return out

    def _write_proposals_only(
        self,
        md: str,
        filename: str,
        *,
        source_session_id: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        proposals_path = self.proposals_dir / filename
        if proposals_path.exists():
            proposals_path.unlink()
        proposals_path.write_text(md, encoding="utf-8")

        entry_id = str(ULID())
        rel_prop = Path("proposals") / filename
        entry = {
            "id": entry_id,
            "op": "PROPOSAL_CREATE",
            "source_session_id": source_session_id,
            "snapshot": [
                {"rel": str(rel_prop).replace("\\", "/"), "before_b64": None, "after_b64": _b64_utf8(md)},
            ],
            "reason": reason,
        }
        self.journal.append(
            entry,
            human_lines=[
                f"### {entry_id} PROPOSAL_CREATE",
                f"- source_session: `{source_session_id}`",
                f"- wrote `rules/{rel_prop.as_posix()}`",
            ],
        )
        return {"mode": "proposal", "path": f"rules/{rel_prop.as_posix()}", "changelog_id": entry_id}

    def promote_rule(self, *, filename: str) -> dict[str, Any]:
        from agent_mcp.security import validate_basename

        fn = validate_basename(filename, suffix=".md")

        proposals_path = (self.proposals_dir / fn).resolve()
        if not proposals_path.is_file():
            raise FileNotFoundError(f"missing proposals file {fn}")

        active_path = (self.active_dir / fn).resolve()
        before_active = active_path.read_text(encoding="utf-8") if active_path.exists() else None

        proposals_bytes = proposals_path.read_bytes()
        promo_md = proposals_bytes.decode("utf-8")
        promoted_rel = proposals_path.relative_to(self.rules_root).as_posix().replace("\\", "/")

        self.active_dir.mkdir(parents=True, exist_ok=True)
        active_path.write_bytes(proposals_bytes)
        proposals_path.unlink(missing_ok=True)

        entry_id = str(ULID())
        snaps = [
            {"rel": f"active/{fn}", "before_b64": _b64_utf8_optional(before_active), "after_b64": _b64_utf8(promo_md)},
            {"rel": promoted_rel, "before_b64": _b64_utf8(promo_md), "after_b64": None},
        ]

        entry = {"id": entry_id, "op": "PROMOTE_RULE", "snapshot": snaps}
        self.journal.append(
            entry,
            human_lines=[
                f"### {entry_id} PROMOTE_RULE",
                f"- promoted `{fn}` proposals → active",
            ],
        )
        self._index_reload()
        return {"changelog_id": entry_id}

    def rollback_rule(self, *, changelog_id: str) -> dict[str, Any]:
        entry = self._find_entry(changelog_id)
        if entry is None:
            raise KeyError(f"changelog id not found: {changelog_id}")
        if str(entry.get("op")) == "ROLLBACK":
            raise ValueError("cannot rollback a rollback entry")

        snaps = list(entry.get("snapshot") or [])
        if not isinstance(snaps, list):
            raise ValueError("invalid changelog entry snapshot")

        for snap in reversed(snaps):
            if not isinstance(snap, dict):
                raise ValueError("invalid snapshot record")
            rel_raw = snap.get("rel")
            if not isinstance(rel_raw, str):
                raise ValueError("snapshot.rel must be a string")
            rel = Path(rel_raw)
            if not rel.parts or rel.parts[0] not in {"active", "proposals"}:
                raise ValueError(f"snapshot targets only active/proposals paths, got `{rel_raw}`")
            if any(p == ".." for p in rel.parts):
                raise ValueError(f"snapshot path contains traversal: `{rel_raw}`")

            tgt = self.rules_root.joinpath(rel)
            tgt.parent.mkdir(parents=True, exist_ok=True)

            before_b64 = snap.get("before_b64")
            if before_b64 is None:
                if tgt.exists():
                    tgt.unlink()
            else:
                txt = _dec_b64_optional(str(before_b64))
                tgt.write_text(txt or "", encoding="utf-8")

        rollback_id = str(ULID())
        rb_entry = {"id": rollback_id, "op": "ROLLBACK", "rolls_back": entry["id"]}

        human = [
            f"### {rollback_id} ROLLBACK",
            f"- restores state before changelog entry `{changelog_id}`",
        ]
        self.journal.append(rb_entry, human_lines=human)
        self._index_reload()
        return {"rollback_id": rollback_id}

    def _find_entry(self, changelog_id: str) -> dict[str, Any] | None:
        if not self.machine_log.is_file():
            return None
        found = None
        with self.machine_log.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                ent = json.loads(line)
                if str(ent.get("id")) == changelog_id:
                    found = ent
        return found
