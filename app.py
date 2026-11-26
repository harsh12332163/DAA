"""Local web server for the Smart Dependency and Project Execution Manager."""

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from algorithms import (
    CycleError,
    dfs_topological_sort,
    kahn_topological_sort,
)


ROOT = Path(__file__).resolve().parent
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/static/": ("index.html", "text/html; charset=utf-8"),
    "/static/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/static/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/static/app.js": ("app.js", "text/javascript; charset=utf-8"),
}
MAX_REQUEST_BYTES = 1_000_000


def build_graph(task_rows):
    """Validate task rows and return prerequisite-to-dependent adjacency lists."""
    if not isinstance(task_rows, list):
        raise ValueError("The request must include a tasks list.")

    names = []
    dependencies_by_task = {}
    for index, row in enumerate(task_rows):
        if not isinstance(row, dict):
            raise ValueError("Each task must be an object.")
        name = row.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Every task needs a non-empty name.")
        name = name.strip()
        if len(name) > 80:
            raise ValueError("Task names must be 80 characters or fewer.")
        if name in dependencies_by_task:
            raise ValueError("Task names must be unique: " + name)

        dependencies = row.get("dependencies", [])
        if not isinstance(dependencies, list) or not all(
            isinstance(dependency, str) for dependency in dependencies
        ):
            raise ValueError("Dependencies must be a list of task names.")
        names.append(name)
        dependencies_by_task[name] = [dependency.strip() for dependency in dependencies]

    graph = {name: [] for name in names}
    for task, dependencies in dependencies_by_task.items():
        for dependency in dependencies:
            if dependency not in graph:
                raise ValueError(
                    "Unknown dependency '" + dependency + "' used by '" + task + "'."
                )
            if task not in graph[dependency]:
                graph[dependency].append(task)
    return graph


def timed_sort(sort_function, graph):
    start = time.perf_counter()
    order = sort_function(graph)
    return order, (time.perf_counter() - start) * 1000


def analyze_tasks(task_rows):
    graph = build_graph(task_rows)
    dependency_count = sum(len(neighbors) for neighbors in graph.values())
    results = {}
    cycle = None

    for key, sort_function in (
        ("kahn", kahn_topological_sort),
        ("dfs", dfs_topological_sort),
    ):
        try:
            order, elapsed_ms = timed_sort(sort_function, graph)
            results[key] = {"order": order, "timeMs": round(elapsed_ms, 4)}
        except CycleError as error:
            results[key] = {"order": None}
            if key == "dfs":
                results[key]["cycle"] = list(error.cycle)
                cycle = list(error.cycle)
            else:
                results[key]["blocked"] = list(error.cycle)

    return {
        "taskCount": len(graph),
        "dependencyCount": dependency_count,
        "cycle": cycle,
        "results": results,
    }


def benchmark_graph(size):
    """Build a reproducible sparse DAG with a chain and short forward edges."""
    graph = {str(index): [] for index in range(size)}
    for index in range(size - 1):
        graph[str(index)].append(str(index + 1))
        if index + 5 < size:
            graph[str(index)].append(str(index + 5))
    return graph


def benchmark():
    rows = []
    for size in (100, 500, 1000, 2000):
        graph = benchmark_graph(size)
        row = {
            "taskCount": size,
            "dependencyCount": sum(len(neighbors) for neighbors in graph.values()),
        }
        for key, sort_function in (
            ("kahnMs", kahn_topological_sort),
            ("dfsMs", dfs_topological_sort),
        ):
            start = time.perf_counter()
            for _ in range(5):
                sort_function(graph)
            row[key] = round((time.perf_counter() - start) * 1000 / 5, 4)
        rows.append(row)
    return {"runs": rows}


class ProjectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/health":
            self.send_json(200, {"status": "ok"})
            return
        if path not in STATIC_FILES:
            self.send_error(404)
            return

        filename, content_type = STATIC_FILES[path]
        content = (ROOT / "static" / filename).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ("/api/analyze", "/api/benchmark"):
            self.send_error(404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("Request body must be no larger than 1 MB.")
            body = self.rfile.read(length)
            payload = json.loads(body) if body else {}
            if path == "/api/benchmark":
                result = benchmark()
            else:
                if not isinstance(payload, dict):
                    raise ValueError("The request body must be a JSON object.")
                result = analyze_tasks(payload.get("tasks"))
            self.send_json(200, result)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
            self.send_json(400, {"error": str(error)})

    def send_json(self, status, payload):
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format_string, *args):
        print("%s - %s" % (self.address_string(), format_string % args))


def main():
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), ProjectHandler)
    print("Smart Dependency Manager running at http://%s:%d" % (host, port))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
