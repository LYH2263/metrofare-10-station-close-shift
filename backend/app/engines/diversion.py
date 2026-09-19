def resolve_actual(code: str, stations_by_code: dict[str, dict]) -> str:
    """Map a requested station code to the code actually used for routing.

    A closed station diverts to its designated ``divert_to`` station. Follows
    the chain defensively (a divert target may itself have been closed later);
    stops on a missing target or a cycle and returns the last code seen.
    """
    seen = set()
    cur = code
    while True:
        st = stations_by_code.get(cur)
        if not st or not st.get("closed"):
            return cur
        nxt = st.get("divert_to")
        if not nxt or nxt in seen:
            return cur
        seen.add(cur)
        cur = nxt
