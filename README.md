# aspath-graph

Turn a pile of AS paths into a picture. Paste the output of `show ip bgp <prefix>` from a looking
glass (or a list of paths, one per line) and get a Graphviz graph of how the prefix is reached,
with thicker edges for the hops more paths go through.

Python 3.10+, standard library only. You need Graphviz (`dot`) to render the output.

## Usage

```
./aspath_graph.py examples/paths.txt | dot -Tsvg > paths.svg
./aspath_graph.py examples/show_ip_bgp.txt --highlight 6939 | dot -Tpng > lg.png
```

From a looking glass over ssh:

```
ssh lg.example.net 'show ip bgp 192.0.2.0/24' | ./aspath_graph.py --rankdir TB | dot -Tsvg -o out.svg
```

Input formats:

- **plain**: one path per line, ASNs separated by spaces; an origin code (`i`, `e`, `?`) at the
  end is fine
- **`show ip bgp`**: detected from the `Network ... Path` header; the path is read from that column
  so the metric / local-pref / weight numbers are not mistaken for ASNs

Prepends are collapsed (`1299 1299 1299` becomes one hop) unless you pass `--keep-prepends`, and
AS_SETs from aggregates (`{64510,64511}`) are dropped. Origin ASes are shaded blue, `--highlight`
ones yellow.

## Tests

```
python3 -m unittest discover -s tests
```
