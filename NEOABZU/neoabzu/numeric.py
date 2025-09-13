"""Thin wrapper around the Rust-based numeric module."""

from neoabzu_numeric import cosine_similarity, find_principal_components

__all__ = ["find_principal_components", "cosine_similarity"]
