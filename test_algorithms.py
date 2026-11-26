import unittest

from algorithms import (
    CycleError,
    dfs_topological_sort,
    kahn_topological_sort,
)
from app import analyze_tasks, benchmark, build_graph


class TopologicalSortTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "plan": ["build", "design"],
            "design": ["build"],
            "build": ["test"],
            "test": [],
            "independent": [],
        }

    def assert_valid_order(self, order):
        positions = {node: index for index, node in enumerate(order)}
        for prerequisite, dependents in self.graph.items():
            for dependent in dependents:
                self.assertLess(positions[prerequisite], positions[dependent])
        self.assertEqual(set(order), set(self.graph))

    def test_kahn_and_dfs_produce_valid_topological_orders(self):
        self.assert_valid_order(kahn_topological_sort(self.graph))
        self.assert_valid_order(dfs_topological_sort(self.graph))

    def test_both_algorithms_reject_cycles(self):
        graph = {"a": ["b"], "b": ["c"], "c": ["a"]}
        for sort_function in (kahn_topological_sort, dfs_topological_sort):
            with self.subTest(algorithm=sort_function.__name__):
                with self.assertRaises(CycleError):
                    sort_function(graph)

    def test_dfs_reports_a_closed_cycle_path(self):
        with self.assertRaises(CycleError) as context:
            dfs_topological_sort({"a": ["b"], "b": ["c"], "c": ["a"]})
        self.assertEqual(context.exception.cycle[0], context.exception.cycle[-1])

    def test_iterative_dfs_handles_deep_dependency_chains(self):
        graph = {str(index): [str(index + 1)] for index in range(1499)}
        graph["1499"] = []
        order = dfs_topological_sort(graph)
        self.assertEqual(order[0], "0")
        self.assertEqual(order[-1], "1499")


class TaskAnalysisTests(unittest.TestCase):
    def test_build_graph_converts_prerequisites_to_outgoing_edges(self):
        graph = build_graph([
            {"name": "Design", "dependencies": []},
            {"name": "Build", "dependencies": ["Design"]},
        ])
        self.assertEqual(graph, {"Design": ["Build"], "Build": []})

    def test_unknown_dependency_is_reported(self):
        with self.assertRaisesRegex(ValueError, "Unknown dependency"):
            build_graph([{"name": "Build", "dependencies": ["Design"]}])

    def test_analysis_returns_both_orders_and_graph_metrics(self):
        result = analyze_tasks([
            {"name": "Design", "dependencies": []},
            {"name": "Build", "dependencies": ["Design"]},
        ])
        self.assertEqual(result["taskCount"], 2)
        self.assertEqual(result["dependencyCount"], 1)
        self.assertIsNone(result["cycle"])
        self.assertEqual(result["results"]["kahn"]["order"], ["Design", "Build"])
        self.assertEqual(result["results"]["dfs"]["order"], ["Design", "Build"])

    def test_analysis_reports_a_cycle_without_scheduling(self):
        result = analyze_tasks([
            {"name": "A", "dependencies": ["B"]},
            {"name": "B", "dependencies": ["A"]},
            {"name": "Blocked behind cycle", "dependencies": ["A"]},
        ])
        self.assertIsNotNone(result["cycle"])
        self.assertIsNone(result["results"]["kahn"]["order"])
        self.assertIsNone(result["results"]["dfs"]["order"])
        self.assertIn("Blocked behind cycle", result["results"]["kahn"]["blocked"])
        cycle_path = result["results"]["dfs"]["cycle"]
        self.assertEqual(cycle_path[0], cycle_path[-1])

    def test_benchmark_sizes_and_results(self):
        result = benchmark()
        self.assertEqual([run["taskCount"] for run in result["runs"]], [100, 500, 1000, 2000])
        self.assertTrue(all(run["kahnMs"] >= 0 and run["dfsMs"] >= 0 for run in result["runs"]))


if __name__ == "__main__":
    unittest.main()
