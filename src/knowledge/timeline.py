"""
⚡ ABANGCOLEK Timeline Engine
Implements Section 26 of CHAT5.md (Business Timeline Engine).
Produces chronologically sorted timelines with complete evidentiary links.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from .graph import KnowledgeGraph


class TimelineBuilder:
    """
    Constructs, filters, and exports chronologically structured business timelines
    anchored in empirical evidence.
    """

    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        db_path: Optional[Union[str, Path]] = None,
    ):
        self.kg = knowledge_graph or KnowledgeGraph(db_path=db_path)

    def get_timeline(self, ascending: bool = True) -> List[Dict[str, Any]]:
        """Returns the full timeline sorted chronologically."""
        return self.kg.get_timeline(ascending=ascending)

    def filter_by_date_range(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        ascending: bool = True,
    ) -> List[Dict[str, Any]]:
        """Filters timeline events within a specified ISO date range (YYYY-MM-DD)."""
        all_events = self.get_timeline(ascending=ascending)
        filtered = []
        for ev in all_events:
            date_str = ev.get("event_date", "")[:10]
            if start_date and date_str < start_date:
                continue
            if end_date and date_str > end_date:
                continue
            filtered.append(ev)
        return filtered

    def filter_by_entity(
        self,
        entity_id: str,
        ascending: bool = True,
    ) -> List[Dict[str, Any]]:
        """Filters timeline events that involve a specific entity_id."""
        all_events = self.get_timeline(ascending=ascending)
        return [
            ev for ev in all_events
            if entity_id in ev.get("entity_ids", [])
        ]

    def filter_by_confidence(
        self,
        min_confidence: float = 0.8,
        ascending: bool = True,
    ) -> List[Dict[str, Any]]:
        """Filters events with confidence >= min_confidence."""
        all_events = self.get_timeline(ascending=ascending)
        return [
            ev for ev in all_events
            if ev.get("confidence", 0.0) >= min_confidence
        ]

    def export_markdown(self, ascending: bool = True) -> str:
        """
        Exports the timeline into a standardized GitHub Flavored Markdown document
        with clickable evidence anchors and involved entities.
        """
        events = self.get_timeline(ascending=ascending)
        lines = [
            "# 📅 ABANGCOLEK Verified Business Timeline",
            "",
            "> Chronologically reconstructed corporate, product, and incident evolution.",
            "> Every event is backed by cryptographic SHA-256 evidence provenance.",
            "",
            "| Event Date | Title | Key Entities | Evidence Links | Confidence |",
            "| :--- | :--- | :--- | :--- | :---: |",
        ]

        for ev in events:
            date_str = ev.get("event_date", "N/A")[:10]
            title = ev.get("title", "Untitled")
            entities = ", ".join([f"`{e}`" for e in ev.get("entity_ids", [])])
            ev_links = ", ".join([f"[`{e_id}`](#{e_id})" for e_id in ev.get("evidence_ids", [])])
            conf = f"{ev.get('confidence', 1.0) * 100:.0f}%"
            lines.append(f"| **{date_str}** | {title} | {entities} | {ev_links} | {conf} |")

        lines.append("")
        lines.append("## Event Detail Log")
        lines.append("")
        for ev in events:
            lines.append(f"### 📍 {ev.get('event_date', '')[:10]} — {ev.get('title')}")
            lines.append(f"- **Event ID**: `{ev.get('event_id')}`")
            lines.append(f"- **Description**: {ev.get('description')}")
            lines.append(f"- **Involved Entities**: {', '.join(ev.get('entity_ids', []))}")
            lines.append(f"- **Supporting Evidence IDs**: {', '.join(ev.get('evidence_ids', []))}")
            lines.append(f"- **Confidence**: {ev.get('confidence', 1.0)}")
            lines.append("")

        return "\n".join(lines)

    def export_json(
        self,
        output_path: Optional[Union[str, Path]] = None,
        ascending: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Exports the chronologically sorted timeline to JSON.
        Optionally writes to disk if output_path is provided.
        """
        events = self.get_timeline(ascending=ascending)
        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
        return events
