import sys
from pathlib import Path

import numpy as np
import pytest
from OpenSSL import crypto

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI.rfa_7d import RFA7D


def _gen_keys():
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)
    priv = crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey)
    pub = crypto.dump_publickey(crypto.FILETYPE_PEM, pkey)
    return priv, pub


def test_tampered_grid_fails_execution():
    priv, pub = _gen_keys()
    core = RFA7D()
    core.sign_core(priv, pub)
    core.grid = np.copy(core.grid)
    core.grid.flat[0] += 1  # tamper with data
    vec = [0j] * core.grid.size
    with pytest.raises(RuntimeError):
        core.execute(vec)


def test_valid_grid_executes():
    priv, pub = _gen_keys()
    core = RFA7D()
    core.sign_core(priv, pub)
    vec = [1 + 0j] * core.grid.size
    out = core.execute(vec)
    assert out.shape == core.shape
