"""Geo-referenced land graph utilities.

This module stores a lightweight knowledge graph using ``networkx`` with
optional ``geopandas`` support. Nodes typically represent sites with
longitude/latitude coordinates; edges represent paths between sites.

The `docs/nazarick_agents.md` guide provides broader architectural context.
"""

from __future__ import annotations

import json
from typing import Dict, Tuple

import networkx as nx

try:  # ``geopandas`` is optional
    import geopandas as gpd
    from shapely.geometry import Point
except Exception:  # pragma: no cover - optional dependency
    gpd = None
    Point = None


class GeoKnowledge:
    """Graph wrapper with optional GeoPandas support."""

    def __init__(self) -> None:
        self.graph = nx.Graph()

    def add_site(self, node_id: str, *, lon: float, lat: float, **attrs: float) -> None:
        """Add a site node to the graph."""
        data = {"lon": float(lon), "lat": float(lat), **attrs}
        self.graph.add_node(node_id, **data)

    def add_path(self, a: str, b: str, **attrs: float) -> None:
        """Add an edge between two sites."""
        self.graph.add_edge(a, b, **attrs)

    def to_jsonl(self, path: str) -> None:
        """Export nodes and edges to a JSONL file."""
        with open(path, "w", encoding="utf-8") as fh:
            for node, data in self.graph.nodes(data=True):
                entry = {"type": "node", "id": node, **data}
                fh.write(json.dumps(entry) + "\n")
            for a, b, data in self.graph.edges(data=True):
                entry = {"type": "edge", "source": a, "target": b, **data}
                fh.write(json.dumps(entry) + "\n")

    @classmethod
    def from_jsonl(cls, path: str) -> "GeoKnowledge":
        """Reconstruct a graph from a JSONL file."""
        gk = cls()
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                item = json.loads(line)
                kind = item.pop("type", None)
                if kind == "node":
                    node_id = item.pop("id")
                    gk.graph.add_node(node_id, **item)
                elif kind == "edge":
                    src = item.pop("source")
                    dst = item.pop("target")
                    gk.graph.add_edge(src, dst, **item)
        return gk

    def nearest_ritual_site(self, lon: float, lat: float) -> Tuple[str, Dict]:
        """Return the ritual site closest to the provided coordinates."""
        ritual_nodes = [
            (n, d)
            for n, d in self.graph.nodes(data=True)
            if d.get("category") == "ritual_site"
        ]
        if not ritual_nodes:
            raise ValueError("No ritual sites found")

        def dist(data: Dict) -> float:
            return (lon - data["lon"]) ** 2 + (lat - data["lat"]) ** 2

        node, data = min(ritual_nodes, key=lambda nd: dist(nd[1]))
        return node, data

    def to_geodataframe(self):
        """Return a GeoDataFrame of nodes if GeoPandas is installed."""
        if gpd is None or Point is None:
            raise ImportError("geopandas is not installed")
        records = []
        for node, data in self.graph.nodes(data=True):
            record = {**data, "id": node, "geometry": Point(data["lon"], data["lat"])}
            records.append(record)
        return gpd.GeoDataFrame(records, geometry="geometry")
