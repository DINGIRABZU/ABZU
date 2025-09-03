"""Tests for huggingface-backed generation."""

from __future__ import annotations

import importlib
import sys

import torch

import pytest

# Use the real huggingface_hub module instead of the test stub.
sys.modules.pop("huggingface_hub", None)
sys.modules.pop("huggingface_hub.utils", None)
importlib.import_module("huggingface_hub")

from transformers import AutoTokenizer, GPT2LMHeadModel


@pytest.mark.parametrize("model_name", ["distilgpt2"])
def test_generate_returns_text(model_name):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = GPT2LMHeadModel.from_pretrained(model_name)
    model.to(device)

    prompt = "Hello world"
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = model.generate(**inputs, max_length=20)

    # Decode and ensure new tokens are generated beyond the prompt length
    generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    assert len(generated) > len(prompt)
