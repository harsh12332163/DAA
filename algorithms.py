"""Topological sorting algorithms for directed task-dependency graphs."""

from collections import deque
from collections.abc import Mapping, Sequence


class CycleError(ValueError):
    """Raised when a dependency graph contains a directed cycle."""

    def __init__(self, cycle: Sequence[str], *, is_path=True):
        self.cycle = tuple(cycle)
        if is_path:
            message = "Cycle detected: " + " -> ".join(self.cycle)
        else:
            message = "Cycle prevents scheduling; unresolved tasks: " + ", ".join(self.cycle)
        super().__init__(message)


Graph = Mapping[str, Sequence[str]]


def kahn_topological_sort(graph: Graph) -> list[str]:
    """Return a topological ordering using Kahn's BFS-based algorithm."""
    indegree = {node: 0 for node in graph}
    for neighbors in graph.values():
        for neighbor in neighbors:
            indegree[neighbor] += 1

    ready = deque(node for node in graph if indegree[node] == 0)
    order = []

    while ready:
        node = ready.popleft()
        order.append(node)
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                ready.append(neighbor)

    if len(order) != len(graph):
        remaining = [node for node in graph if indegree[node] > 0]
        raise CycleError(remaining, is_path=False)
    return order


def dfs_topological_sort(graph: Graph) -> list[str]:
    """Return a topological ordering using iterative depth-first search."""
    state = {node: 0 for node in graph}  # 0 = unseen, 1 = active, 2 = complete
    order = []

    for start in graph:
        if state[start] != 0:
            continue

        state[start] = 1
        active = [start]
        active_position = {start: 0}
        stack = [(start, iter(graph[start]))]

        while stack:
            node, neighbors = stack[-1]
            try:
                neighbor = next(neighbors)
            except StopIteration:
                stack.pop()
                active.pop()
                active_position.pop(node)
                state[node] = 2
                order.append(node)
                continue

            if state[neighbor] == 0:
                state[neighbor] = 1
                active_position[neighbor] = len(active)
                active.append(neighbor)
                stack.append((neighbor, iter(graph[neighbor])))
            elif state[neighbor] == 1:
                cycle = active[active_position[neighbor]:] + [neighbor]
                raise CycleError(cycle)

    order.reverse()
    return order
