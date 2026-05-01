from server.topomap import TopoMap


def test_add_node_returns_incrementing_ids():
    tm = TopoMap()
    n0 = tm.add_node(photo_path="a.jpg", detected=["bread"], summary="bakery")
    n1 = tm.add_node(photo_path="b.jpg", detected=["milk"], summary="dairy")
    assert n0 == 0
    assert n1 == 1


def test_add_edge_records_action():
    tm = TopoMap()
    a = tm.add_node(photo_path="a.jpg", detected=[], summary="")
    b = tm.add_node(photo_path="b.jpg", detected=[], summary="")
    tm.add_edge(a, b, action="walked left")
    edges = list(tm.graph.edges(data=True))
    assert len(edges) == 1
    assert edges[0][0] == a
    assert edges[0][1] == b
    assert edges[0][2]["action"] == "walked left"


def test_to_dict_serializes_graph():
    tm = TopoMap()
    a = tm.add_node(photo_path="a.jpg", detected=["x"], summary="s1")
    b = tm.add_node(photo_path="b.jpg", detected=["y"], summary="s2")
    tm.add_edge(a, b, action="forward")
    d = tm.to_dict(current_node=b, goal_node=None)
    assert d["nodes"][0]["id"] == 0
    assert d["nodes"][1]["detected"] == ["y"]
    assert d["edges"][0] == {"from": 0, "to": 1, "action": "forward"}
    assert d["current_node"] == b
    assert d["goal_node"] is None
