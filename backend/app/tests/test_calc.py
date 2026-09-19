from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_hops, shortest_path
from app.engines.route_quote import quote_route

EDGES = [("A1", "A2"), ("A2", "A3"), ("A2", "B1"), ("B1", "B2")]
RULES = [{"max_hops": 2, "price": 3.0}, {"max_hops": 4, "price": 4.0}, {"max_hops": None, "price": 6.0}]


def test_hops_a1_a3():
    assert shortest_hops(EDGES, "A1", "A3") == 2


def test_hops_a1_b2():
    assert shortest_hops(EDGES, "A1", "B2") == 3


def test_fare_by_hops():
    assert fare_for_hops(2, RULES) == 3.0
    assert fare_for_hops(3, RULES) == 4.0
    assert fare_for_hops(10, RULES) == 6.0


def test_quote():
    q = quote_route(EDGES, "A1", "B2", RULES)
    assert q["hops"] == 3 and q["fare"] == 4.0


def test_shortest_path():
    assert shortest_path(EDGES, "A1", "B2") == ["A1", "A2", "B1", "B2"]
    assert shortest_path(EDGES, "A1", "A1") == ["A1"]
    assert shortest_path(EDGES, "A1", "ZZ") is None


def test_quote_reports_path_and_actual_codes():
    q = quote_route(EDGES, "A1", "B2", RULES)
    assert q["actual_start"] == "A1" and q["actual_end"] == "B2"
    assert q["path"] == ["A1", "A2", "B1", "B2"]
    assert q["rerouted"] is False and q["detours"] == []


def test_quote_reroutes_closed_end():
    closures = {"A3": {"reroute_to": "A2", "closed_reason": "施工"}}
    q = quote_route(EDGES, "A1", "A3", RULES, closures)
    assert q["end"] == "A3" and q["actual_end"] == "A2"
    assert q["hops"] == 1 and q["fare"] == 3.0
    assert q["path"] == ["A1", "A2"]
    assert q["rerouted"] is True
    assert q["detours"] == [{"from": "A3", "to": "A2"}]


def test_quote_reroutes_closed_start():
    closures = {"A1": {"reroute_to": "A2", "closed_reason": "积水"}}
    q = quote_route(EDGES, "A1", "B2", RULES, closures)
    assert q["start"] == "A1" and q["actual_start"] == "A2"
    assert q["hops"] == 2 and q["path"] == ["A2", "B1", "B2"]


def test_quote_without_closure_unaffected():
    q = quote_route(EDGES, "A1", "A3", RULES, {"B2": {"reroute_to": "B1"}})
    assert q["hops"] == 2 and q["rerouted"] is False
