from __future__ import annotations

__version__ = "0.1.0"

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Mapping
import networkx as nx

try:
    import yaml
except Exception as exc:
    raise RuntimeError("pyyaml is required for planning engine") from exc


def _load_graph(p: Path) -> nx.DiGraph:
    return nx.node_link_graph(json.loads(p.read_text(encoding="utf-8")), edges="links")


def _load_priorities(p: Path) -> Mapping[str, int]:
    if not p.exists():
        return {}
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    out: Dict[str, int] = {}
    for n, m in raw.items():
        pr = m.get("priority")
        if isinstance(pr, str) and pr.upper().startswith("P"):
            try:
                out[n] = int(pr[1:])
            except ValueError:
                pass
    return out


def _load_success_rates(p: Path) -> Mapping[str, float]:
    if not p.exists():
        return {}
    suc: Dict[str, int] = defaultdict(int)
    tot: Dict[str, int] = defaultdict(int)
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        c = str(r.get("component"))
        s = str(r.get("status", "")).lower()
        tot[c] += 1
        if s == "success":
            suc[c] += 1
    return {c: suc[c] / t for c, t in tot.items() if t}


def _dependency_order(g: nx.DiGraph, n: str) -> List[str]:
    d = nx.descendants(g, n)
    sub = g.subgraph(d | {n})
    return list(nx.topological_sort(sub.reverse()))


def _criticality(g: nx.DiGraph, n: str) -> int:
    return len(nx.descendants(g.reverse(), n))


def _score(p: int, c: int, s: float) -> float:
    return float(p) + c + s


def plan(
    knowledge_path: Path | None = None,
    *,
    output: Path | None = None,
    log_path: Path | None = None,
    priorities_path: Path | None = None,
) -> Dict[str, Dict[str, object]]:
    root = Path(__file__).resolve().parents[2]
    knowledge_path = knowledge_path or root / "logs" / "razar_knowledge.json"
    output = output or root / "logs" / "razar_plans.json"
    log_path = log_path or root / "logs" / "razar.log"
    priorities_path = priorities_path or root / "docs" / "component_priorities.yaml"
    g = _load_graph(knowledge_path)
    pr = _load_priorities(priorities_path)
    sr = _load_success_rates(log_path)
    plans: Dict[str, Dict[str, object]] = {}
    for node in g.nodes:
        name = Path(str(node)).stem
        steps = _dependency_order(g, node)
        p = pr.get(name, 0)
        c = _criticality(g, node)
        s = sr.get(name, 0.0)
        plans[name] = {
            "component": str(node),
            "steps": steps,
            "priority": p,
            "criticality": c,
            "success_rate": s,
            "score": _score(p, c, s),
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plans, indent=2), encoding="utf-8")
    return plans


def main() -> None:  # pragma: no cover
    plan()


if __name__ == "__main__":  # pragma: no cover
    main()
