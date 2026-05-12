"""Navigation engine: converts product queries into step-by-step directions."""
from __future__ import annotations

from typing import List, Optional

import networkx as nx

from server.store_knowledge import LocationMatch, find_product
from server.store_map import (
    NODE_BACK_WALL,
    NODE_ENTRANCE,
    NODE_LEFT_FRESH,
    NODE_LEFT_HOTPOT,
    get_store_topomap,
)


def _zone_to_node(zone_name: str) -> int:
    """Map a zone name to its node ID."""
    return {
        "entrance": NODE_ENTRANCE,
        "left_wall_fresh": NODE_LEFT_FRESH,
        "left_wall_hotpot": NODE_LEFT_HOTPOT,
        "back_wall": NODE_BACK_WALL,
    }[zone_name]


def navigate_to_product(
    query: str,
    start_node: int = NODE_ENTRANCE,
) -> Optional[dict]:
    """Find a product and return step-by-step navigation directions.

    Returns a dict with:
        query, matched_products, location, location_zh,
        directions, aisle_number, zone, confidence
    Or None if no match found.
    """
    matches = find_product(query)
    if not matches:
        return None

    best: LocationMatch = matches[0]
    topo = get_store_topomap()

    # Determine target node
    if best.location_type == "aisle" and best.aisle_number is not None:
        target_node = best.aisle_number  # aisle N = node N
    elif best.location_type == "zone" and best.zone_name is not None:
        target_node = _zone_to_node(best.zone_name)
    else:
        return None

    # Find shortest path
    try:
        path = nx.shortest_path(topo.graph, source=start_node, target=target_node)
    except nx.NetworkXNoPath:
        return None

    # Build step-by-step directions
    directions: List[str] = []
    if start_node == NODE_ENTRANCE:
        directions.append("Start at the store entrance (入口)")

    for i in range(len(path) - 1):
        edge_data = topo.graph.edges[path[i], path[i + 1]]
        directions.append(edge_data["action"])

    # Final instruction
    if best.location_type == "aisle":
        directions.append(
            f"Turn into Aisle {best.aisle_number} — "
            f"look for {best.matched_keyword} "
            f"({best.display_zh.split(' - ', 1)[-1]})"
        )
    else:
        directions.append(
            f"You've arrived at the {best.display_en} — "
            f"look for {best.matched_keyword}"
        )

    # Collect all matched keywords for top results
    matched_products = list(dict.fromkeys(m.matched_keyword for m in matches[:5]))

    return {
        "query": query,
        "matched_products": matched_products,
        "location": best.display_en,
        "location_zh": best.display_zh,
        "directions": directions,
        "aisle_number": best.aisle_number,
        "zone": best.zone_name,
        "confidence": round(best.confidence, 3),
    }
