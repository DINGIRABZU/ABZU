import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "SPIRAL_OS"))

from qnl_engine import parse_input


def test_parse_input_keyword_low_urgency():
    data = parse_input("remember our memory soon?")
    assert data == {
        "type": "question",
        "object": "text",
        "tone": "Memory",
        "urgency": "low",
        "linked_memory": None,
    }


def test_parse_input_glyph_and_memory_link():
    data = parse_input("Summon ❣⟁ now! #3")
    assert data == {
        "type": "statement",
        "object": "glyph_sequence",
        "tone": "Longing",
        "urgency": "high",
        "linked_memory": "3",
    }


def test_parse_input_keyword_default():
    data = parse_input("joy awakens")
    assert data == {
        "type": "statement",
        "object": "text",
        "tone": "Joy",
        "urgency": "normal",
        "linked_memory": None,
    }
