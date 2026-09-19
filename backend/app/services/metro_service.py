from app.db import connect
from app.engines.route_quote import quote_route
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo


class StationClosureError(ValueError):
    """Raised when a close/unclose request violates closure rules."""


class MetroService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def stations(self, include_closed: bool = False):
        if include_closed:
            return stations_repo.list_all(self._conn)
        return stations_repo.list_open(self._conn)

    def station(self, code: str):
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        return [{"a": a, "b": b} for a, b in edges_repo.list_pairs(self._conn)]

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def quote(self, start: str, end: str, persist: bool):
        edges = edges_repo.list_pairs(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        closures = stations_repo.closed_map(self._conn)
        result = quote_route(edges, start, end, rules, closures)
        run_id = None
        if persist and result.get("reachable"):
            run_id = runs_repo.insert(self._conn, "quote", {"start": start, "end": end}, result)
        return {"run_id": run_id, **result}

    def close_station(self, code: str, reroute_to: str | None, reason: str):
        station = stations_repo.get_by_code(self._conn, code)
        if not station:
            raise StationClosureError("station_not_found")
        if station["closed"]:
            raise StationClosureError("already_closed")
        if not reroute_to:
            raise StationClosureError("reroute_missing")
        target = stations_repo.get_by_code(self._conn, reroute_to)
        if not target:
            raise StationClosureError("reroute_missing")
        if target["closed"]:
            raise StationClosureError("reroute_closed")
        adjacent = any(
            {a, b} == {code, reroute_to} for a, b in edges_repo.list_pairs(self._conn)
        )
        if not adjacent:
            raise StationClosureError("reroute_not_adjacent")
        stations_repo.set_closure(self._conn, code, reroute_to, reason or "")
        return stations_repo.get_by_code(self._conn, code)

    def unclose_station(self, code: str):
        station = stations_repo.get_by_code(self._conn, code)
        if not station:
            raise StationClosureError("station_not_found")
        if not station["closed"]:
            raise StationClosureError("not_closed")
        stations_repo.clear_closure(self._conn, code)
        return stations_repo.get_by_code(self._conn, code)

    def history(self, limit=50):
        return runs_repo.list_recent(self._conn, limit)

    def dashboard(self):
        st = stations_repo.list_all(self._conn)
        clean = [s for s in st if "种子" not in s["name"]]
        dirty = [s for s in st if "种子" in s["name"]]
        return {
            "station_count": len(st),
            "edge_count": len(edges_repo.list_pairs(self._conn)),
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
        }
