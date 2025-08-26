"""Smoke tests for core package and SciPy."""

from __future__ import annotations


def test_scipy_sparse_available():
    from scipy import sparse

    matrix = sparse.csr_matrix([[0]])
    assert matrix.shape == (1, 1)


def test_core_available():
    import core

    assert hasattr(core, "__file__")
