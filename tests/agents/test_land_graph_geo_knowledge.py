"""Tests for land graph geo knowledge."""

from agents.land_graph.geo_knowledge import GeoKnowledge


def build_sample_graph():
    gk = GeoKnowledge()
    gk.add_site("ritual", lon=0.0, lat=0.0, category="ritual_site")
    gk.add_site("village", lon=1.0, lat=1.0, category="village")
    gk.add_path("ritual", "village", distance=1.5)
    return gk


def test_jsonl_roundtrip(tmp_path):
    gk = build_sample_graph()
    path = tmp_path / "graph.jsonl"
    gk.to_jsonl(path)

    loaded = GeoKnowledge.from_jsonl(path)
    assert set(loaded.graph.nodes) == {"ritual", "village"}
    assert loaded.graph.edges["ritual", "village"]["distance"] == 1.5


def test_nearest_ritual_site():
    gk = build_sample_graph()
    node, data = gk.nearest_ritual_site(lon=0.2, lat=0.1)
    assert node == "ritual"
    assert data["category"] == "ritual_site"
