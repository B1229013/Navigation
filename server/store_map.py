"""Pre-built topological map of the Carrefour store from image data."""
from __future__ import annotations

from server.topomap import TopoMap
from server.store_knowledge import AISLES, ZONES

# Node ID assignments:
#   0        = Entrance
#   1 .. 18  = Aisle entrances (aisle number = node id)
#   19       = Back wall (frozen / alcohol)
#   20       = Left wall - fresh produce
#   21       = Left wall - hotpot / refrigerated

NODE_ENTRANCE = 0
NODE_BACK_WALL = 19
NODE_LEFT_FRESH = 20
NODE_LEFT_HOTPOT = 21


def build_store_topomap() -> TopoMap:
    """Build the complete topological map of the Carrefour store.

    Returns a TopoMap with ~22 nodes representing key locations and edges
    encoding walking directions along the main corridor and perimeter.
    """
    topo = TopoMap()

    # --- Node 0: Entrance ---
    nid = topo.add_node(
        photo_path="",
        detected=["entrance", "promotions", "water", "drinks"],
        summary="Store entrance - promotional displays, bulk water & drinks",
    )
    assert nid == NODE_ENTRANCE

    # --- Nodes 1-18: Aisle entrances ---
    for aisle in AISLES:
        cats_en = " / ".join(aisle.categories_en)
        cats_zh = " / ".join(aisle.categories_zh)
        nid = topo.add_node(
            photo_path="",
            detected=aisle.categories_en[:4],
            summary=f"Aisle {aisle.number} ({cats_zh}) - {cats_en}",
        )
        assert nid == aisle.number

    # --- Node 19: Back wall ---
    nid = topo.add_node(
        photo_path="",
        detected=["frozen food", "ice cream", "beer", "alcohol"],
        summary="Back wall - Frozen food (冷凍), ice cream, beer & alcohol",
    )
    assert nid == NODE_BACK_WALL

    # --- Node 20: Left wall - fresh produce ---
    nid = topo.add_node(
        photo_path="",
        detected=["vegetables", "fruits", "fresh produce"],
        summary="Left wall - Fresh produce, fruits & vegetables (生鮮蔬果)",
    )
    assert nid == NODE_LEFT_FRESH

    # --- Node 21: Left wall - hotpot / refrigerated ---
    nid = topo.add_node(
        photo_path="",
        detected=["hotpot", "meat", "refrigerated", "tofu"],
        summary="Left wall - Hotpot ingredients, fresh meat & refrigerated (火鍋/冷藏)",
    )
    assert nid == NODE_LEFT_HOTPOT

    # --- Edges: Main corridor (entrance → aisle 1 → 2 → ... → 18) ---
    topo.add_edge(NODE_ENTRANCE, 1,
                  action="Walk straight into the store along the main corridor")
    for i in range(1, 18):
        topo.add_edge(i, i + 1,
                      action=f"Continue along the main corridor past Aisle {i}")

    # Reverse edges for walking back
    for i in range(18, 1, -1):
        topo.add_edge(i, i - 1,
                      action=f"Walk back along the main corridor toward Aisle {i - 1}")
    topo.add_edge(1, NODE_ENTRANCE,
                  action="Walk back to the entrance")

    # --- Edges: Main corridor → Back wall ---
    topo.add_edge(18, NODE_BACK_WALL,
                  action="Continue past Aisle 18 to the back wall (frozen food area)")
    topo.add_edge(NODE_BACK_WALL, 18,
                  action="Walk from the back wall toward Aisle 18")

    # --- Edges: Back wall → Left wall ---
    topo.add_edge(NODE_BACK_WALL, NODE_LEFT_HOTPOT,
                  action="Turn left along the back wall toward the hotpot/refrigerated section")
    topo.add_edge(NODE_LEFT_HOTPOT, NODE_BACK_WALL,
                  action="Walk right along the back wall toward frozen food")

    # --- Edges: Left wall hotpot → Left wall fresh ---
    topo.add_edge(NODE_LEFT_HOTPOT, NODE_LEFT_FRESH,
                  action="Continue along the left wall toward fresh produce")
    topo.add_edge(NODE_LEFT_FRESH, NODE_LEFT_HOTPOT,
                  action="Walk along the left wall toward the hotpot section")

    # --- Edges: Left wall fresh → Entrance ---
    topo.add_edge(NODE_LEFT_FRESH, NODE_ENTRANCE,
                  action="Continue along the left wall back to the entrance")
    topo.add_edge(NODE_ENTRANCE, NODE_LEFT_FRESH,
                  action="Turn left from the entrance toward the fresh produce section")

    return topo


# Module-level singleton
_store_map: TopoMap | None = None


def get_store_topomap() -> TopoMap:
    """Get or create the singleton store topological map."""
    global _store_map
    if _store_map is None:
        _store_map = build_store_topomap()
    return _store_map
