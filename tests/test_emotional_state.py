"""Tests for emotional state."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import os
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import emotional_state


def test_state_persistence(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(emotional_state, "STATE_FILE", state_file)
    emotional_state._STATE.clear()
    emotional_state._save_state()

    pairs = [(440.0, 880.0), (333.0, 666.0)]
    emotional_state.set_resonance_pairs(pairs)
    emotional_state.set_soul_state("awakened")

    data = json.loads(state_file.read_text())
    assert data["resonance_pairs"] == [[440.0, 880.0], [333.0, 666.0]]
    assert data["soul_state"] == "awakened"

    emotional_state._STATE.clear()
    emotional_state._load_state()
    assert emotional_state.get_resonance_pairs() == pairs
    assert emotional_state.get_soul_state() == "awakened"


def test_current_layer_round_trip(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(emotional_state, "STATE_FILE", state_file)
    emotional_state._STATE.clear()
    emotional_state._save_state()

    emotional_state.set_current_layer("citrinitas_layer")
    data = json.loads(state_file.read_text())
    assert data["current_layer"] == "citrinitas_layer"

    emotional_state._STATE.clear()
    emotional_state._load_state()
    assert emotional_state.get_current_layer() == "citrinitas_layer"


def test_soul_state_without_manager(monkeypatch):
    """set_soul_state should work even if the optional manager is missing."""

    monkeypatch.setattr(emotional_state, "soul_state_manager", None)
    emotional_state._STATE.clear()
    emotional_state.set_soul_state("dreaming")
    assert emotional_state.get_soul_state() == "dreaming"


def test_encrypt_decrypt_without_aes(monkeypatch):
    """_encrypt/_decrypt should act as passthrough when AESGCM is unavailable."""

    monkeypatch.setattr(emotional_state, "AESGCM", None)
    monkeypatch.delenv("EMOTION_AES_KEY", raising=False)
    os.environ["EMOTION_AES_KEY"] = "00" * 32
    data = b"secret"
    enc = emotional_state._encrypt(data)
    assert enc == data  # no encryption without AESGCM
    dec = emotional_state._decrypt(enc)
    assert dec == data
