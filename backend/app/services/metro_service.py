from app.db import connect
from app.engines.diversion import resolve_actual
from app.engines.route_quote import quote_route
from app.repositories import edges as edges_repo
from app.repositories import fare_rules as rules_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo


class MetroService:
    def __init__(self, conn=None):
        self._conn = conn or connect()

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

    def close_station(self, code: str, divert_to: str, reason: str = ""):
        st = stations_repo.get_by_code(self._conn, code)
        if not st:
            raise ValueError("站点不存在")
        if st["closed"]:
            raise ValueError("站点已封闭")
        if not divert_to:
            raise ValueError("必须指定改到站")
        if divert_to == code:
            raise ValueError("改到站不能是本站")
        target = stations_repo.get_by_code(self._conn, divert_to)
        if not target:
            raise ValueError("改到站不存在")
        if target["closed"]:
            raise ValueError("改到站已封闭")
        pairs = edges_repo.list_pairs(self._conn)
        if not any({a, b} == {code, divert_to} for a, b in pairs):
            raise ValueError("改到站必须与该站直接邻接")
        stations_repo.set_closed(self._conn, code, divert_to, reason or "")
        return stations_repo.get_by_code(self._conn, code)

    def unclose_station(self, code: str):
        st = stations_repo.get_by_code(self._conn, code)
        if not st:
            raise ValueError("站点不存在")
        if not st["closed"]:
            raise ValueError("站点未封闭")
        stations_repo.set_open(self._conn, code)
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        return [{"a": a, "b": b} for a, b in edges_repo.list_pairs(self._conn)]

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def quote(self, start: str, end: str, persist: bool):
        stations = {s["code"]: s for s in stations_repo.list_all(self._conn)}
        actual_start = resolve_actual(start, stations)
        actual_end = resolve_actual(end, stations)
        edges = edges_repo.list_pairs(self._conn)
        rules = rules_repo.as_calc_rules(self._conn)
        result = quote_route(edges, actual_start, actual_end, rules)
        payload = {
            "start": start,
            "end": end,
            "actual_start": actual_start,
            "actual_end": actual_end,
            "diverted": actual_start != start or actual_end != end,
            "path": result["path"],
            "hops": result["hops"],
            "fare": result["fare"],
            "reachable": result["reachable"],
        }
        run_id = None
        if persist and payload["reachable"]:
            run_id = runs_repo.insert(self._conn, "quote", {"start": start, "end": end}, payload)
        return {"run_id": run_id, **payload}

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
