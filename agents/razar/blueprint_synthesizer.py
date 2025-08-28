from __future__ import annotations

"""Build a component dependency graph from Markdown blueprints.

The synthesizer walks ``docs/system_blueprint.md`` and
``docs/component_index.md`` along with every markdown file linked from them.
A directed graph is produced where edges represent markdown links between
documents. The graph is exported in node-link JSON format for later planning.
"""

import json
import re
from pathlib import Path
from typing import Iterable, Set

import networkx as nx

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _extract_links(markdown: str) -> Iterable[str]:
    """Yield relative links from a markdown document."""

    for match in LINK_RE.finditer(markdown):
        target = match.group(1).strip()
        # Ignore external or anchor links
        if target.startswith("http") or target.startswith("#"):
            continue
        yield target


def _resolve_links(path: Path) -> Set[Path]:
    """Return resolved paths for local markdown links."""

    text = path.read_text(encoding="utf-8")
    links: Set[Path] = set()
    for href in _extract_links(text):
        candidate = (path.parent / href).resolve()
        if candidate.exists():
            links.add(candidate)
    return links


def build_graph(start_docs: Iterable[Path]) -> nx.DiGraph:
    """Recursively build a dependency graph from ``start_docs``."""

    graph: nx.DiGraph = nx.DiGraph()
    visited: Set[Path] = set()

    def visit(doc: Path) -> None:
        if doc in visited:
            return
        visited.add(doc)
        graph.add_node(str(doc))
        for linked in _resolve_links(doc):
            graph.add_edge(str(doc), str(linked))
            if linked.suffix.lower() in {".md", ".markdown"}:
                visit(linked)

    for d in start_docs:
        visit(d.resolve())
    return graph


def export_graph(graph: nx.DiGraph, output: Path) -> None:
    """Write ``graph`` to ``output`` in node-link JSON format."""

    output.parent.mkdir(parents=True, exist_ok=True)
    data = nx.node_link_data(graph, edges="links")
    output.write_text(json.dumps(data, indent=2), encoding="utf-8")


def synthesize(output: Path | None = None) -> nx.DiGraph:
    """Build the dependency graph and optionally persist it.

    Parameters
    ----------
    output:
        Path to the JSON file. Defaults to ``logs/razar_knowledge.json``.
    """

    root = Path(__file__).resolve().parents[2]
    docs = [
        root / "docs" / "system_blueprint.md",
        root / "docs" / "component_index.md",
        root / "docs" / "nazarick_manifesto.md",
    ]
    graph = build_graph(docs)
    if output is None:
        output = root / "logs" / "razar_knowledge.json"
    export_graph(graph, output)
    return graph
