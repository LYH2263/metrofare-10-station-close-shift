import sqlite3


def list_all(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM stations ORDER BY code").fetchall()]


def list_open(conn: sqlite3.Connection) -> list[dict]:
    q = "SELECT * FROM stations WHERE closed=0 ORDER BY code"
    return [dict(r) for r in conn.execute(q).fetchall()]


def get_by_code(conn: sqlite3.Connection, code: str) -> dict | None:
    row = conn.execute("SELECT * FROM stations WHERE code=?", (code,)).fetchone()
    return dict(row) if row else None


def set_closed(conn: sqlite3.Connection, code: str, divert_to: str, reason: str) -> None:
    conn.execute(
        "UPDATE stations SET closed=1, divert_to=?, closed_reason=? WHERE code=?",
        (divert_to, reason, code),
    )
    conn.commit()


def set_open(conn: sqlite3.Connection, code: str) -> None:
    conn.execute(
        "UPDATE stations SET closed=0, divert_to=NULL, closed_reason=NULL WHERE code=?",
        (code,),
    )
    conn.commit()
