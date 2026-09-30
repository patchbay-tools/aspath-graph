import os
import unittest

from aspath_graph import parse_paths, to_dot

HERE = os.path.dirname(os.path.abspath(__file__))


def example(name):
    with open(os.path.join(HERE, "..", "examples", name), encoding="utf-8") as fh:
        return fh.readlines()


class ParseTest(unittest.TestCase):
    def test_plain_paths_collapse_prepends(self):
        paths = parse_paths(example("paths.txt"))
        self.assertEqual(paths[1], [3356, 1299, 64500])
        self.assertEqual(paths[4], [6939, 64501])

    def test_keep_prepends(self):
        paths = parse_paths(example("paths.txt"), keep_prepends=True)
        self.assertEqual(paths[1], [3356, 1299, 1299, 1299, 64500])

    def test_as_prefixed_tokens(self):
        paths = parse_paths(["AS3356 as1299 AS64500 i\n", "ASX 174 64500\n"])
        self.assertEqual(paths, [[3356, 1299, 64500], [174, 64500]])

    def test_show_ip_bgp_ignores_metric_columns(self):
        paths = parse_paths(example("show_ip_bgp.txt"))
        self.assertEqual(paths, [
            [174, 2914, 64500],
            [3356, 1299, 64500],
            [6939, 64500],
            [3356, 64501],
            [6939, 64501],
        ])


class DotTest(unittest.TestCase):
    def test_edges_and_highlight(self):
        dot = to_dot([[174, 64500], [6939, 64500], [174, 64500]], highlight={6939})
        self.assertTrue(dot.startswith("digraph aspaths {"))
        self.assertIn('AS174 -> AS64500 [penwidth=4.00, tooltip="2 paths"];', dot)
        self.assertIn('AS6939 [label="AS6939", fillcolor="#ffd966"];', dot)
        self.assertIn('AS64500 [label="AS64500", fillcolor="#cfe2f3"];', dot)


if __name__ == "__main__":
    unittest.main()
