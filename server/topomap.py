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
