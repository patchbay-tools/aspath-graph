#!/usr/bin/env python3
"""Render AS paths into a Graphviz graph.

Input is either one AS path per line::

    3356 1299 64500
    174 64500

or the table from ``show ip bgp`` on a Cisco/FRR/Quagga looking glass,
where the path is read from the column under the ``Path`` header.
"""

import argparse
import re
import sys
from collections import Counter

ORIGIN_CODES = {"i", "e", "?"}
AS_SET_RE = re.compile(r"[{\[].*?[}\]]")


def clean_path(tokens: list[str], keep_prepends: bool = False) -> list[int]:
    path = []
    for token in tokens:
        if token in ORIGIN_CODES:
            break
        if not token.isdigit():
            continue
        asn = int(token)
        if not keep_prepends and path and path[-1] == asn:
            continue
        path.append(asn)
    return path


def parse_paths(lines, keep_prepends: bool = False) -> list[list[int]]:
    """Parse plain paths or ``show ip bgp`` output into lists of ASNs."""
    paths = []
    path_column = None

    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue

        if path_column is None and "Network" in line and "Path" in line:
            path_column = line.index("Path")
            continue

        if path_column is not None:
            # only route lines carry a path; status/banner lines are shorter
            if len(line) <= path_column:
                continue
            text = line[path_column:]
        else:
            text = line

        # AS_SETs ({64500,64501}) are an aggregate, not a hop we can draw
        tokens = AS_SET_RE.sub(" ", text).split()
        path = clean_path(tokens, keep_prepends)
        if path:
            paths.append(path)

    return paths


def to_dot(paths: list[list[int]], highlight: set[int], rankdir: str = "LR") -> str:
    edges = Counter()
    nodes = set()
    origins = set()

    for path in paths:
        nodes.update(path)
        origins.add(path[-1])
        for left, right in zip(path, path[1:]):
            if left != right:
                edges[(left, right)] += 1

    heaviest = max(edges.values(), default=1)
    out = [
        "digraph aspaths {",
        f"  rankdir={rankdir};",
        '  node [shape=box, style="rounded,filled", fillcolor="#f4f4f4", fontname="Helvetica"];',
        '  edge [color="#555555"];',
    ]

    for asn in sorted(nodes):
        attrs = [f'label="AS{asn}"']
        if asn in highlight:
            attrs.append('fillcolor="#ffd966"')
        elif asn in origins:
            attrs.append('fillcolor="#cfe2f3"')
        out.append(f"  AS{asn} [{', '.join(attrs)}];")

    for (left, right), count in sorted(edges.items()):
        width = 1 + 3 * count / heaviest
        out.append(f'  AS{left} -> AS{right} [penwidth={width:.2f}, tooltip="{count} paths"];')

    out.append("}")
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render AS paths as Graphviz DOT.")
    parser.add_argument("input", nargs="?", default="-", help="paths file (default: stdin)")
    parser.add_argument("--highlight", action="append", default=[], metavar="ASN",
                        help="colour this AS (repeatable)")
    parser.add_argument("--keep-prepends", action="store_true",
                        help="keep repeated ASNs instead of collapsing prepends")
    parser.add_argument("--rankdir", default="LR", choices=["LR", "TB", "RL", "BT"])
    args = parser.parse_args()

    if args.input == "-":
        paths = parse_paths(sys.stdin, args.keep_prepends)
    else:
        with open(args.input, encoding="utf-8") as fh:
            paths = parse_paths(fh, args.keep_prepends)

    if not paths:
        print("no AS paths found in input", file=sys.stderr)
        return 1

    highlight = {int(a.upper().removeprefix("AS")) for a in args.highlight}
    sys.stdout.write(to_dot(paths, highlight, args.rankdir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
