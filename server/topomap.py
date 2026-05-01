"""Topological map: nodes are photo locations, edges are movement actions."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import networkx as nx


class TopoMap:
    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self._next_id: int = 0

    def add_node(self, photo_path: str, detected: List[str], summary: str) -> int:
        nid = self._next_id
        self._next_id += 1
        self.graph.add_node(
            nid,
            photo_path=photo_path,
            detected=detected,
            summary=summary,
            timestamp=datetime.utcnow().isoformat(),
        )
        return nid

    def add_edge(self, from_id: int, to_id: int, action: str) -> None:
        self.graph.add_edge(from_id, to_id, action=action)

    def to_dict(self, current_node: Optional[int], goal_node: Optional[int]) -> dict:
        nodes = [
            {
                "id": nid,
                "photo": data["photo_path"],
                "detected": data["detected"],
                "summary": data["summary"],
                "timestamp": data["timestamp"],
            }
            for nid, data in self.graph.nodes(data=True)
        ]
        edges = [
            {"from": u, "to": v, "action": data["action"]}
            for u, v, data in self.graph.edges(data=True)
        ]
        return {
            "nodes": nodes,
            "edges": edges,
            "current_node": current_node,
            "goal_node": goal_node,
        }

    def summarize_for_vlm(self, current_id: int) -> str:
        """Walk from start to current, produce <150-word prose summary for the VLM."""
        if self.graph.number_of_nodes() == 0:
            return "No locations visited yet."

        try:
            start = next(n for n in self.graph.nodes if self.graph.in_degree(n) == 0)
        except StopIteration:
            start = 0

        if start == current_id:
            data = self.graph.nodes[current_id]
            return f"You are at the starting location. Visible: {data['summary']}."

        try:
            path = nx.shortest_path(self.graph, source=start, target=current_id)
        except nx.NetworkXNoPath:
            path = [current_id]

        parts: List[str] = []
        for i, nid in enumerate(path):
            node = self.graph.nodes[nid]
            label = node["summary"] or ", ".join(node["detected"][:3]) or f"location {nid}"
            if i == 0:
                parts.append(f"Started at {label}")
            else:
                action = self.graph.edges[path[i - 1], nid]["action"]
                parts.append(f"{action}, arrived at {label}")
        return ". ".join(parts) + "."
