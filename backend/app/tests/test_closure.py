import json
import sqlite3

import pytest

from app.services.metro_service import MetroService

EDGES = [("A1", "A2"), ("A2", "A3"), ("A2", "B1"), ("B1", "B2")]


def make_service() -> MetroService:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE stations(
            id INTEGER PRIMARY KEY, code TEXT, name TEXT,
            closed INTEGER NOT NULL DEFAULT 0, divert_to TEXT, closed_reason TEXT);
        CREATE TABLE edges(a TEXT, b TEXT);
        CREATE TABLE fare_rules(id INTEGER PRIMARY KEY, max_hops INTEGER, price REAL);
        CREATE TABLE calc_runs(
            id INTEGER PRIMARY KEY, kind TEXT, input_json TEXT, result_json TEXT, created_at TEXT);
        """
    )
    for code, name in [("A1", "城站"), ("A2", "市心"), ("A3", "东湾"), ("B1", "北苑"), ("B2", "机场")]:
        conn.execute("INSERT INTO stations(code, name) VALUES (?,?)", (code, name))
    for a, b in EDGES:
        conn.execute("INSERT INTO edges(a,b) VALUES (?,?)", (a, b))
    conn.executemany(
        "INSERT INTO fare_rules(max_hops, price) VALUES (?,?)",
        [(2, 3.0), (4, 4.0), (None, 6.0)],
    )
    conn.commit()
    return MetroService(conn)


def test_close_rejects_missing_divert_target():
    with make_service() as s:
        with pytest.raises(ValueError, match="改到站不存在"):
            s.close_station("A3", "ZZ", "施工")


def test_close_rejects_closed_divert_target():
    with make_service() as s:
        s.close_station("B1", "A2", "施工")
        with pytest.raises(ValueError, match="改到站已封闭"):
            s.close_station("A3", "B1", "施工")  # B1 not adjacent to A3 anyway
        with pytest.raises(ValueError, match="改到站已封闭"):
            s.close_station("A2", "B1", "施工")


def test_close_rejects_non_adjacent_divert():
    with make_service() as s:
        with pytest.raises(ValueError, match="直接邻接"):
            s.close_station("A3", "B1", "施工")


def test_close_rejects_self_and_unknown_station():
    with make_service() as s:
        with pytest.raises(ValueError, match="不能是本站"):
            s.close_station("A3", "A3", "施工")
        with pytest.raises(ValueError, match="站点不存在"):
            s.close_station("ZZ", "A2", "施工")


def test_closed_station_hidden_from_default_list_but_reason_readable():
    with make_service() as s:
        s.close_station("A3", "A2", "台风停运")
        codes = [x["code"] for x in s.stations()]
        assert "A3" not in codes
        all_codes = [x["code"] for x in s.stations(include_closed=True)]
        assert "A3" in all_codes
        row = s.station("A3")
        assert row["closed"] == 1
        assert row["closed_reason"] == "台风停运"
        assert row["divert_to"] == "A2"


def test_quote_diverts_and_reports_original_actual_path():
    with make_service() as s:
        s.close_station("A3", "A2", "施工")
        q = s.quote("A1", "A3", persist=False)
        assert q["reachable"] and q["diverted"]
        assert q["start"] == "A1" and q["end"] == "A3"  # 原始编码
        assert q["actual_start"] == "A1" and q["actual_end"] == "A2"  # 实际用的编码
        assert q["path"] == ["A1", "A2"]  # 途经站
        assert q["hops"] == 1 and q["fare"] == 3.0


def test_unclose_restores_original_path():
    with make_service() as s:
        s.close_station("A3", "A2", "施工")
        s.unclose_station("A3")
        q = s.quote("A1", "A3", persist=False)
        assert not q["diverted"]
        assert q["actual_end"] == "A3"
        assert q["path"] == ["A1", "A2", "A3"] and q["hops"] == 2


def test_unclose_requires_closed_station():
    with make_service() as s:
        with pytest.raises(ValueError, match="未封闭"):
            s.unclose_station("A3")


def test_readonly_trial_writes_nothing():
    with make_service() as s:
        before = len(s.history())
        q = s.quote("A1", "B2", persist=False)
        assert q["run_id"] is None
        assert len(s.history()) == before


def test_persisted_record_keeps_actual_codes_after_unclose():
    with make_service() as s:
        s.close_station("A3", "A2", "施工")
        q = s.quote("A1", "A3", persist=True)
        assert q["run_id"] is not None
        s.unclose_station("A3")
        runs = s.history()
        rec = next(r for r in runs if r["id"] == q["run_id"])
        result = json.loads(rec["result_json"])
        assert result["end"] == "A3"  # 原始编码
        assert result["actual_end"] == "A2"  # 当时实际用的编码不被改写
        assert result["path"] == ["A1", "A2"]
