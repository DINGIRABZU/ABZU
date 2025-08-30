# pydocstyle: skip-file
"""VAE-based sacred memory module using PyTorch.

This module defines a lightweight Variational Autoencoder (VAE) that ingests
embeddings representing Physical, Mental, Emotional and Spiritual layers. The
latent vectors and generated artefacts are written to ``data/sacred``.

The public API ``generate_sacred_glyph`` accepts a mapping with layer names and
returns the path to a generated image along with a short phrase derived from the
latent vector.
"""

from __future__ import annotations

__version__ = "0.1.1"

import datetime as _dt
from pathlib import Path
from typing import Dict, Iterable, Tuple

try:  # pragma: no cover - optional dependency
    import torch
    from torch import nn
    from torch.nn import functional as F
except Exception:  # pragma: no cover - optional dependency
    torch = None  # type: ignore
    nn = None  # type: ignore
    F = None  # type: ignore

try:  # pragma: no cover - optional dependency
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None  # type: ignore

from aspect_processor import analyze_phonetic, analyze_semantic, analyze_spatial

SACRED_DIR = Path(__file__).resolve().parent / "data" / "sacred"
SACRED_DIR.mkdir(parents=True, exist_ok=True)


if torch is not None:

    class SacredVAE(nn.Module):
        """Simple fully connected VAE."""

        def __init__(
            self,
            input_dim: int,
            hidden_dim: int = 128,
            latent_dim: int = 32,
            output_dim: int = 28 * 28,
        ) -> None:
            super().__init__()
            self.fc1 = nn.Linear(input_dim, hidden_dim)
            self.fc_mu = nn.Linear(hidden_dim, latent_dim)
            self.fc_logvar = nn.Linear(hidden_dim, latent_dim)
            self.fc_dec1 = nn.Linear(latent_dim, hidden_dim)
            self.fc_dec2 = nn.Linear(hidden_dim, output_dim)

        def encode(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
            h1 = torch.relu(self.fc1(x))
            return self.fc_mu(h1), self.fc_logvar(h1)

        def reparameterize(
            self, mu: torch.Tensor, logvar: torch.Tensor
        ) -> torch.Tensor:
            std = torch.exp(0.5 * logvar)
            eps = torch.randn_like(std)
            return mu + eps * std

        def decode(self, z: torch.Tensor) -> torch.Tensor:
            h3 = torch.relu(self.fc_dec1(z))
            return torch.sigmoid(self.fc_dec2(h3))

        def forward(
            self, x: torch.Tensor
        ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
            mu, logvar = self.encode(x)
            z = self.reparameterize(mu, logvar)
            recon = self.decode(z)
            return recon, mu, logvar, z

else:  # pragma: no cover - dependencies missing

    class SacredVAE:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - stub
            raise RuntimeError("PyTorch is required for SacredVAE")


_MODEL: SacredVAE | None = None


def _get_model(input_dim: int) -> SacredVAE:
    """Return a cached ``SacredVAE`` initialised for ``input_dim``."""

    global _MODEL
    if _MODEL is None:
        if torch is None:  # pragma: no cover - dependency missing
            raise RuntimeError("PyTorch is required to generate sacred glyphs")
        _MODEL = SacredVAE(input_dim)
    return _MODEL


def generate_sacred_glyph(inputs: Dict[str, Iterable[float]]) -> Tuple[Path, str]:
    """Generate a sacred glyph from layer embeddings.

    Parameters
    ----------
    inputs:
        Mapping with keys ``physical``, ``mental``, ``emotional`` and
        ``spiritual`` pointing to iterable numeric embeddings.

    Returns
    -------
    tuple[Path, str]
        Path to the generated image and an associated phrase.
    """

    if torch is None or Image is None:  # pragma: no cover - dependency missing
        raise RuntimeError("PyTorch and Pillow are required to generate glyphs")

    layers = ["physical", "mental", "emotional", "spiritual"]
    vectors = []
    for layer in layers:
        if layer not in inputs:
            raise ValueError(f"missing layer: {layer}")
        vectors.append(torch.tensor(list(inputs[layer]), dtype=torch.float32))

    x = torch.cat(vectors)
    model = _get_model(len(x))
    recon, _, _, z = model(x)
    analyze_spatial(z.detach().cpu().tolist())

    ts = _dt.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    latent_path = SACRED_DIR / f"latent_{ts}.pt"
    image_path = SACRED_DIR / f"artifact_{ts}.png"
    phrase_path = SACRED_DIR / f"phrase_{ts}.txt"

    torch.save(z.detach(), latent_path)

    img = recon.detach().cpu().view(28, 28).numpy()
    img_uint8 = (img * 255).clip(0, 255).astype("uint8")
    Image.fromarray(img_uint8, mode="L").save(image_path)

    phrase = f"Glyph born of latent norm {z.norm().item():.2f}"
    phrase_path.write_text(phrase, encoding="utf-8")

    analyze_phonetic(phrase)
    analyze_semantic(phrase)

    return image_path, phrase


__all__ = ["generate_sacred_glyph", "SacredVAE", "SACRED_DIR"]
