import json
import os
import subprocess
import sys
import time
from pathlib import Path

import grpc
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import importlib.util
import types

neoabzu_vector = types.ModuleType("neoabzu_vector")
neoabzu_vector.search = lambda text, top_n: [(text, 1.0)] * top_n
sys.modules["neoabzu_vector"] = neoabzu_vector

neoabzu_pkg = types.ModuleType("neoabzu")
sys.modules["neoabzu"] = neoabzu_pkg

for name in ["vector_pb2", "vector_pb2_grpc"]:
    spec = importlib.util.spec_from_file_location(
        f"neoabzu.{name}", ROOT / "neoabzu" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    sys.modules[f"neoabzu.{name}"] = module
    sys.modules[name] = module
    setattr(neoabzu_pkg, name, module)

spec = importlib.util.spec_from_file_location(
    "neoabzu.vector", ROOT / "neoabzu" / "vector.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # type: ignore[arg-type]
neoabzu_pkg.vector = module
VectorClient = module.VectorClient


@pytest.mark.component("vector")
def test_grpc_end_to_end(tmp_path):
    store = tmp_path / "store.json"
    json.dump(["alpha", "beta"], store.open("w"))
    env = os.environ.copy()
    env["NEOABZU_VECTOR_STORE"] = str(store)
    server = subprocess.Popen(
        [
            "cargo",
            "run",
            "-p",
            "neoabzu-vector",
            "--bin",
            "server",
        ],
        env=env,
        cwd=ROOT,
    )
    try:
        import socket

        for _ in range(60):
            try:
                with socket.create_connection(("localhost", 50051), timeout=1):
                    break
            except OSError:
                time.sleep(1)
        with VectorClient("http://localhost:50051") as client:
            with pytest.raises(grpc.RpcError) as err:
                client.search("alpha", 1)
            assert err.value.code() == grpc.StatusCode.FAILED_PRECONDITION

            init = client.init()
            assert "loaded" in init.message

            resp = client.search("alpha", 1)
            assert resp.results[0].text == "alpha"
    finally:
        server.terminate()
        server.wait()
