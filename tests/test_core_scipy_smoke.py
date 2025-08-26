"""Smoke test ensuring core package and SciPy are importable."""

from __future__ import annotations


def test_core_and_scipy_available():
    from scipy import sparse
    import core

    matrix = sparse.csr_matrix([[0]])
    assert matrix.shape == (1, 1)
    assert hasattr(core, "__file__")
