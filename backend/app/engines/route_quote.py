from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_path


def _resolve(code: str, closures: dict[str, dict]) -> tuple[str, str | None]:
    """Return (actual_code, rerouted_from). Closed stations detour to their reroute stop."""
    info = closures.get(code)
    if info and info.get("reroute_to"):
        return info["reroute_to"], code
    return code, None


def quote_route(
    edges: list[tuple[str, str]],
    start: str,
    end: str,
    rules: list[dict],
    closures: dict[str, dict] | None = None,
) -> dict:
    closures = closures or {}
    actual_start, start_from = _resolve(start, closures)
    actual_end, end_from = _resolve(end, closures)
    result = {
        "start": start,
        "end": end,
        "actual_start": actual_start,
        "actual_end": actual_end,
        "rerouted": bool(start_from or end_from),
        "detours": [
            {"from": f, "to": t}
            for f, t in ((start_from, actual_start), (end_from, actual_end))
            if f
        ],
    }
    path = shortest_path(edges, actual_start, actual_end)
    if path is None:
        return {**result, "hops": None, "fare": None, "path": [], "reachable": False}
    fare = fare_for_hops(len(path) - 1, rules)
    return {**result, "hops": len(path) - 1, "fare": fare, "path": path, "reachable": True}
