from __future__ import annotations

MOCK_INSIGHTS = {
    "open": {"counts": {"total": 5, "success": 5}},
    "bad": {"counts": {"total": 4, "success": 1}},
    "ugly": {"counts": {"total": 4, "success": 1}},
    "close": {"counts": {"total": 3, "success": 2}},
}

MOCK_INTENTS = {
    "open": {"synonyms": ["unseal"]},
    "bad": {"synonyms": ["awful"]},
    "close": {"synonyms": ["shut"]},
}

MOCK_FEEDBACK = [
    {
        "intent": "open",
        "action": "door",
        "success": True,
        "response_quality": 1.0,
        "memory_overlap": 0.0,
    },
    {
        "intent": "close",
        "action": "door",
        "success": True,
        "response_quality": 0.8,
        "memory_overlap": 0.0,
    },
]
