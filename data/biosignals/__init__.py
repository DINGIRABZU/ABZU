"""Biosignal dataset hashes and helpers."""

from __future__ import annotations

from pathlib import Path
import hashlib

__all__ = ["DATA_DIR", "DATASET_HASHES", "hash_file", "__version__"]

__version__ = "0.1.0"

DATA_DIR = Path(__file__).resolve().parent

DATASET_HASHES = {
    "sample_biosignals.csv": (
        "24542e5cc5e740ddc5698f8df8cac5c4f56ab90abbb4d9b158f424254cbebc0e"
    ),
    "sample_biosignals_alpha.csv": (
        "e727360b97cb18738426700f3a69225c5fa7f8359f6c3ef4d6dc6784efd73ab9"
    ),
    "sample_biosignals_beta.csv": (
        "ef0b058532e7c20117a63a45f81b4210d48e56cd69288572154c7aa6faedda1f"
    ),
    "sample_biosignals_gamma.csv": (
        "7ed983d38a6b552fd7e3940653c878416f3a798d02fc2282f2abed2869c3a981"
    ),
    "sample_biosignals_delta.csv": (
        "d1f2d58cea37c8fdca0446e3a85700dae82b56aa78399bc20de879d4177ea3ac"
    ),
    "sample_biosignals_epsilon.csv": (
        "9b6f665d60e0b79ab2a97fe0bb785f2b65835aa062f367f5c0c2b9d881f82e64"
    ),
    "sample_biosignals_zeta.csv": (
        "56b54f16a126cb748365b644ecddcf46534c53145b778ac78cf0a9ad738e7d4b"
    ),
    "sample_biosignals_theta.csv": (
        "e8adf0ef143981df07d907765d4094a274cf81f0120f260688ddedb31fef93a4"
    ),
    "sample_biosignals_iota.csv": (
        "8a87bd55412e89f2d258b9b36a541d62387a08e4a692eef6d386a2950e57973a"
    ),
    "sample_biosignals_kappa.csv": (
        "cfca34a3c5f8c66edd81159e2c768024f9d7e3f63ec24c18445e16457c6ec0ee"
    ),
    "sample_biosignals_anonymized.jsonl": (
        "59bc304d8322fb1625d330bafd0dabbe5aaf79622d24354127df8943a01eb11c"
    ),
}


def hash_file(path: Path) -> str:
    """Return the SHA256 digest for ``path``."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
