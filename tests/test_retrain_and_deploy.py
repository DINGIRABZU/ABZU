import sys
from types import SimpleNamespace, ModuleType
from datetime import datetime, timedelta
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Provide dummy cryptography modules to satisfy imports
crypto = ModuleType("cryptography")
hazmat = ModuleType("cryptography.hazmat")
primitives = ModuleType("cryptography.hazmat.primitives")
hashes = ModuleType("hashes")
hashes.SHA256 = object
primitives.hashes = hashes
asym = ModuleType("cryptography.hazmat.primitives.asymmetric")
pad = ModuleType("pad")
pad.PKCS1v15 = object
rsa_mod = ModuleType("rsa")
rsa_mod.generate_private_key = lambda *a, **k: None
ser = ModuleType("ser")
ser.load_pem_private_key = lambda *a, **k: SimpleNamespace(sign=lambda *a, **k: b"", public_key=lambda: None)
ser.load_pem_public_key = lambda *a, **k: SimpleNamespace(verify=lambda *a, **k: None)
ser.Encoding = ser.PrivateFormat = ser.PublicFormat = ser.NoEncryption = object
sys.modules.update({
    "cryptography": crypto,
    "cryptography.hazmat": hazmat,
    "cryptography.hazmat.primitives": primitives,
    "cryptography.hazmat.primitives.asymmetric": asym,
    "cryptography.hazmat.primitives.asymmetric.padding": pad,
    "cryptography.hazmat.primitives.asymmetric.rsa": rsa_mod,
    "cryptography.hazmat.primitives.serialization": ser,
})

mlflow_dummy = SimpleNamespace(
    start_run=lambda: None,
    log_param=lambda *a, **k: None,
    log_artifact=lambda *a, **k: None,
    end_run=lambda: None,
)
sys.modules["mlflow"] = mlflow_dummy

from INANNA_AI import retrain_and_deploy
from INANNA_AI import train_soul


def _prepare(tmp_path, monkeypatch):
    model_dir = tmp_path / "models"
    soul_dir = model_dir / "soul"
    soul_dir.mkdir(parents=True)
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    (chroma_dir / "emb").write_text("x")

    dummy_soul = tmp_path / "soul.dna"
    dummy_soul.write_text("dna")

    monkeypatch.setattr(retrain_and_deploy, "CHROMA_DIR", chroma_dir)
    monkeypatch.setattr(retrain_and_deploy.config, "MODELS_DIR", model_dir)
    monkeypatch.setattr(retrain_and_deploy, "SOUL_DIR", soul_dir)
    monkeypatch.setattr(retrain_and_deploy, "SOUL_FILE", dummy_soul)
    monkeypatch.setattr(retrain_and_deploy, "LAST_TRAIN_FILE", soul_dir / "last_trained.txt")

    calls = {}
    monkeypatch.setattr(train_soul, "train_soul", lambda log, iterations: calls.setdefault("trained", iterations))
    ml = SimpleNamespace(
        start_run=lambda: calls.setdefault("start", True),
        log_param=lambda *a, **k: calls.setdefault("param", a),
        log_artifact=lambda *a, **k: calls.setdefault("artifact", a),
        end_run=lambda: calls.setdefault("end", True),
    )
    monkeypatch.setattr(retrain_and_deploy, "mlflow", ml)
    return model_dir, chroma_dir, calls


def test_retrain_creates_artifact(tmp_path, monkeypatch):
    model_dir, chroma_dir, calls = _prepare(tmp_path, monkeypatch)

    retrain_and_deploy.retrain_and_deploy(iterations=1)

    assert calls.get("trained") == 1
    artifacts = list((model_dir / "soul").glob("*/soul.dna"))
    assert artifacts
    assert (model_dir / "soul" / "last_trained.txt").exists()


def test_skip_when_no_new_embeddings(tmp_path, monkeypatch):
    model_dir, chroma_dir, calls = _prepare(tmp_path, monkeypatch)
    past = datetime.utcnow() - timedelta(days=1)
    file_path = chroma_dir / "emb"
    os.utime(file_path, (past.timestamp(), past.timestamp()))
    retrain_and_deploy.LAST_TRAIN_FILE.write_text(datetime.utcnow().isoformat())

    retrain_and_deploy.retrain_and_deploy(iterations=1)

    assert "trained" not in calls

