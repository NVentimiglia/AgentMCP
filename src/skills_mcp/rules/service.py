from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from ulid import ULID

from skills_mcp.app_state import AppContext
from skills_mcp.rules.loader import ActiveRuleIndex
from skills_mcp.rules.schema import RuleFrontmatter


class RulesService:
    """Write new Markdown rules directly under ``paths.rules``."""

    def __init__(self, app: AppContext, active_index: ActiveRuleIndex | None = None) -> None:
        self.rules_dir = app.rules_dir
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
        md = f"---\n{dump}\n---\n\n"

        from skills_mcp.security import slugify_trigger

        slug = slugify_trigger(trigger)
        filename = f"{now}-{slug}.md".replace(":", "-")
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        rule_path = self.rules_dir / filename
        if rule_path.exists():
            rule_path.unlink()
        rule_path.write_text(md, encoding="utf-8")

        self._index_reload()
        return {"path": f"rules/{filename}", "rule_id": rid}
