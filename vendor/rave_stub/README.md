# rave shim

The original RAVE audio package is not published on PyPI, yet Stage B rehearsals
expect ``import rave`` to succeed. This shim provides a tiny ``RAVE`` class that
mirrors the encode/decode interface used by the DSP engine so rehearsals can run
on CPU-only hosts without pulling large model dependencies.
