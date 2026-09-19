import json
import os
import pathlib
import tempfile

_TMP = tempfile.mkdtemp()
os.environ["DATA_DIR"] = _TMP  # must precede app imports

import pytest

from app import seed
from app.config import DB_FILENAME
from app.services.metro_service import MetroService, StationClosureError


@pytest.fixture(autouse=True)
def fresh_db():
    p = pathlib.Path(_TMP) / DB_FILENAME
    if p.exists():
        p.unlink()
    seed.init_db()
    yield


def test_close_station_success():
    with MetroService() as s:
        st = s.close_station("A3", "A2", "站台施工")
        assert st["closed"] == 1
        assert st["reroute_to"] == "A2"
        assert st["closed_reason"] == "站台施工"


def test_close_rejects_missing_reroute():
    with MetroService() as s:
        with pytest.raises(StationClosureError):
            s.close_station("A3", None, "施工")
        with pytest.raises(StationClosureError):
            s.close_station("A3", "ZZ", "施工")


def test_close_rejects_non_adjacent_reroute():
    with MetroService() as s:
        with pytest.raises(StationClosureError):
            s.close_station("A3", "B2", "施工")  # A3 与 B2 无直接邻接


def test_close_rejects_closed_reroute():
    with MetroService() as s:
        s.close_station("A3", "A2", "施工")
        with pytest.raises(StationClosureError):
            s.close_station("A2", "A3", "施工")  # 改到站自身已封闭


def test_close_rejects_double_close():
    with MetroService() as s:
        s.close_station("A3", "A2", "施工")
        with pytest.raises(StationClosureError):
            s.close_station("A3", "A2", "施工")


def test_closed_station_hidden_from_default_list_but_readable():
    with MetroService() as s:
        s.close_station("A3", "A2", "站台施工")
        assert "A3" not in {x["code"] for x in s.stations()}
        assert "A3" in {x["code"] for x in s.stations(include_closed=True)}
        row = s.station("A3")
        assert row["closed"] == 1 and row["closed_reason"] == "站台施工"


def test_quote_uses_reroute_and_reports_codes():
    with MetroService() as s:
        s.close_station("A3", "A2", "施工")
        q = s.quote("A1", "A3", persist=False)
        assert q["end"] == "A3" and q["actual_end"] == "A2"
        assert q["hops"] == 1 and q["path"] == ["A1", "A2"]
        assert q["detours"] == [{"from": "A3", "to": "A2"}]


def test_unclose_restores_original_path():
    with MetroService() as s:
        s.close_station("A3", "A2", "施工")
        assert s.quote("A1", "A3", persist=False)["hops"] == 1
        s.unclose_station("A3")
        q = s.quote("A1", "A3", persist=False)
        assert q["hops"] == 2 and q["actual_end"] == "A3"
        assert q["path"] == ["A1", "A2", "A3"] and q["rerouted"] is False


def test_readonly_trial_not_persisted():
    with MetroService() as s:
        before = len(s.history())
        q = s.quote("A1", "B2", persist=False)
        assert q["run_id"] is None
        assert len(s.history()) == before


def test_persisted_record_keeps_actual_codes_after_unclose():
    with MetroService() as s:
        s.close_station("A3", "A2", "施工")
        q = s.quote("A1", "A3", persist=True)
        assert q["run_id"] is not None
        s.unclose_station("A3")
        rec = next(r for r in s.history() if r["id"] == q["run_id"])
        result = json.loads(rec["result_json"])
        assert result["end"] == "A3"
        assert result["actual_end"] == "A2"  # 解封后不回写历史记录
        assert result["path"] == ["A1", "A2"]
