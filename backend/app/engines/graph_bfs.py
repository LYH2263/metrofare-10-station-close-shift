from collections import defaultdict, deque


def shortest_hops(edges: list[tuple[str, str]], start: str, end: str) -> int | None:
    """Undirected graph BFS hop count; None if unreachable."""
    path = shortest_path(edges, start, end)
    return None if path is None else len(path) - 1


def shortest_path(edges: list[tuple[str, str]], start: str, end: str) -> list[str] | None:
    """Undirected graph BFS shortest path as station codes; None if unreachable."""
    if start == end:
        return [start]
    g: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        g[a].add(b)
        g[b].add(a)
    if start not in g or end not in g:
        return None
    q = deque([(start, [start])])
    seen = {start}
    while q:
        cur, path = q.popleft()
        for nxt in sorted(g[cur]):
            if nxt in seen:
                continue
            nxt_path = path + [nxt]
            if nxt == end:
                return nxt_path
            seen.add(nxt)
            q.append((nxt, nxt_path))
    return None
