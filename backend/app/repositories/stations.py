import sqlite3


def list_all(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM stations ORDER BY code").fetchall()]


def list_open(conn: sqlite3.Connection) -> list[dict]:
    q = "SELECT * FROM stations WHERE closed=0 ORDER BY code"
    return [dict(r) for r in conn.execute(q).fetchall()]


def get_by_code(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute("SELECT * FROM stations WHERE code=?", (code,)).fetchone()
    return dict(row) if row else None


def closed_map(conn: sqlite3.Connection) -> dict[str, dict]:
    """code -> {reroute_to, closed_reason} for every closed station."""
    rows = conn.execute("SELECT code, reroute_to, closed_reason FROM stations WHERE closed=1").fetchall()
    return {r["code"]: {"reroute_to": r["reroute_to"], "closed_reason": r["closed_reason"]} for r in rows}


def set_closure(conn: sqlite3.Connection, code: str, reroute_to: str, reason: str) -> None:
    conn.execute(
        "UPDATE stations SET closed=1, reroute_to=?, closed_reason=? WHERE code=?",
        (reroute_to, reason, code),
    )
    conn.commit()


def clear_closure(conn: sqlite3.Connection, code: str) -> None:
    conn.execute(
        "UPDATE stations SET closed=0, reroute_to=NULL, closed_reason=NULL WHERE code=?",
        (code,),
    )
    conn.commit()
