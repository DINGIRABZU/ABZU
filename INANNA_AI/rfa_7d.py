"""Random Field Array 7D with quantum-like execution and DNA serialization."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Sequence

import numpy as np
from .gates import sign_blob, verify_blob

try:  # optional quantum library
    import qutip
except Exception:  # pragma: no cover - optional dependency
    qutip = None  # type: ignore

logger = logging.getLogger(__name__)


class RFA7D:
    """Represent a 7-dimensional grid of complex numbers."""

    def __init__(self, shape: Sequence[int] | None = None) -> None:
        self.shape = tuple(shape) if shape is not None else (2,) * 7
        self.grid = np.random.rand(*self.shape) + 1j * np.random.rand(*self.shape)
        self.integrity_hash = hashlib.sha3_256(self.grid.tobytes()).hexdigest()
        self.signature: bytes | None = None
        self.public_key: bytes | None = None
        logger.debug("Initialized RFA7D with shape %s", self.shape)

    def execute(self, input_vector: Sequence[complex], noise: bool = False) -> np.ndarray:
        """Return the grid scaled by ``input_vector`` with optional noise."""
        if not self.verify_integrity():
            raise RuntimeError("Integrity check failed")

        vec = np.asarray(input_vector, dtype=np.complex128)
        flat = self.grid.ravel()
        if vec.size != flat.size:
            raise ValueError(f"input_vector must have {flat.size} elements")
        result = flat * vec
        if noise and qutip is not None:
            try:
                noise_vec = np.array(qutip.rand_ket(len(result)).full()).ravel()
                result += noise_vec
            except Exception as exc:  # pragma: no cover - external call may fail
                logger.warning("Noise generation failed: %s", exc)
        return result.reshape(self.shape)

    def verify_integrity(self) -> bool:
        """Check whether the grid and signature match the stored values."""
        current = hashlib.sha3_256(self.grid.tobytes()).hexdigest()
        if current != self.integrity_hash:
            return False
        if self.signature and self.public_key:
            return verify_blob(current.encode("utf-8"), self.signature, self.public_key)
        return True

    def sign_core(self, private_key_pem: bytes, public_key_pem: bytes) -> bytes:
        """Sign the current grid hash and store the signature."""
        self.public_key = public_key_pem
        payload = self.integrity_hash.encode("utf-8")
        self.signature = sign_blob(payload, private_key_pem)
        return self.signature

    def encode_to_dna(self) -> str:
        """Serialize the grid to a DNA-like string and save it."""
        byte_data = self.grid.tobytes()
        mapping = {0b00: "A", 0b01: "C", 0b10: "G", 0b11: "T"}
        dna_chars = []
        for byte in byte_data:
            for shift in (6, 4, 2, 0):
                dna_chars.append(mapping[(byte >> shift) & 0b11])
        dna_str = "".join(dna_chars)
        out_path = Path(__file__).resolve().parents[1] / "INANNA_AI" / "soul.dna"
        out_path.write_text(dna_str, encoding="utf-8")
        logger.info("Encoded grid to DNA at %s", out_path)
        return dna_str


__all__ = ["RFA7D"]
