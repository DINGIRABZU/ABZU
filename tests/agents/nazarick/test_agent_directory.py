from agents.nazarick.service_launcher import AgentDirectory, REGISTRY_FILE


def test_lookup_by_chakra():
    directory = AgentDirectory.from_file(REGISTRY_FILE)
    agents = directory.get_by_chakra("heart")
    ids = [a["id"] for a in agents]
    assert ids == ["memory_scribe"]


def test_lookup_by_capability():
    directory = AgentDirectory.from_file(REGISTRY_FILE)
    agents = directory.get_by_capability("prompt_routing")
    ids = [a["id"] for a in agents]
    assert ids == ["prompt_orchestrator"]
