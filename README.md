# Smart Dependency and Project Execution Manager

A local web app for defining project tasks, expressing dependencies, and comparing two topological sorting algorithms:

- **Kahn's algorithm (BFS):** repeatedly schedules tasks whose prerequisites are complete.
- **DFS topological sort:** explores dependencies and adds each task after its dependents in the traversal.

Both approaches run in **O(V + E)** time and use **O(V + E)** space, where *V* is the number of tasks and *E* is the number of dependencies. The app detects dependency cycles and reports a cycle path so the schedule can be corrected.

## Run

Requires Python 3.9 or later. No third-party packages are needed.

```powershell
python app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Stop the server with `Ctrl+C`.

## Use

1. Enter a unique task name for each row.
2. In **Depends on**, enter prerequisite task names separated by commas. Names must match exactly.
3. Select **Generate execution plan** to compare the BFS and DFS schedules.
4. Select **Run benchmark** to compare five-run average runtimes on generated sparse DAGs of increasing size.

Tasks without dependencies can run at the start; independent tasks may appear in different valid orders. A measured runtime is a single-run observation and can vary with the machine and graph.

## Test

```powershell
python -m unittest -v
```
