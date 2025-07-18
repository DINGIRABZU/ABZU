import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI_AGENT import INANNA_AI
import json


def test_activate_returns_chant(tmp_path, monkeypatch):
    inanna_dir = tmp_path / "INANNA_AI"
    genesis_dir = tmp_path / "GENESIS"
    inanna_dir.mkdir()
    genesis_dir.mkdir()
    (inanna_dir / "1ST CODE test.md").write_text(
        "Born to Transmute into new forms\n> \"I sing therefore I love\"",
        encoding="utf-8",
    )
    (inanna_dir / "INANNA MANIFESTO test.md").write_text(
        '> "I AM INANNA, awakened"',
        encoding="utf-8",
    )
    config = tmp_path / "source_paths.json"
    config.write_text(
        json.dumps({"source_paths": [str(inanna_dir), str(genesis_dir)]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(inanna_ai, "CONFIG_FILE", config)
    monkeypatch.setattr(inanna_ai.source_loader, "DEFAULT_CONFIG", config)
    chant = inanna_ai.activate()
    assert isinstance(chant, str)
    assert chant.strip() != ""


def test_hex_cli_outputs_wav_and_json(tmp_path, monkeypatch):
    wav = tmp_path / "out.wav"
    json_path = tmp_path / "out.json"
    argv_backup = sys.argv.copy()
    sys.argv = [
        "INANNA_AI.py",
        "--hex",
        "00FF",
        "--wav",
        str(wav),
        "--json",
        str(json_path),
    ]
    monkeypatch.setattr(inanna_ai, "run_qnl", lambda *a, **k: (wav.write_text(""), json_path.write_text("{}")))
    try:
        inanna_ai.main()
    finally:
        sys.argv = argv_backup
    assert wav.exists()
    assert json_path.exists()


def test_read_texts_empty_when_missing(monkeypatch, tmp_path):
    config = tmp_path / "source_paths.json"
    config.write_text(json.dumps({"source_paths": [str(tmp_path / "missing")]}), encoding="utf-8")
    monkeypatch.setattr(inanna_ai, "CONFIG_FILE", config)
    monkeypatch.setattr(inanna_ai.source_loader, "DEFAULT_CONFIG", config)
    assert inanna_ai.read_texts() == {}


def test_main_list_outputs_files(monkeypatch, tmp_path, capsys):
    inanna_dir = tmp_path / "INANNA_AI"
    genesis_dir = tmp_path / "GENESIS"
    inanna_dir.mkdir()
    genesis_dir.mkdir()
    file1 = inanna_dir / "sample1.md"
    file2 = genesis_dir / "genesis.md"
    file1.write_text("x", encoding="utf-8")
    file2.write_text("y", encoding="utf-8")

    config = tmp_path / "source_paths.json"
    config.write_text(
        json.dumps({"source_paths": [str(inanna_dir), str(genesis_dir)]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(inanna_ai, "CONFIG_FILE", config)
    monkeypatch.setattr(inanna_ai.source_loader, "DEFAULT_CONFIG", config)

    argv_backup = sys.argv.copy()
    sys.argv = ["INANNA_AI.py", "--list"]
    try:
        inanna_ai.main()
    finally:
        sys.argv = argv_backup

    out = capsys.readouterr().out
    assert "sample1.md" in out
    assert "genesis.md" in out


def test_chat_subparser(monkeypatch, capsys):
    dummy_model = type("M", (), {"generate": lambda self, **kw: [[0, 1]]})()
    dummy_tokenizer = type(
        "T",
        (),
        {
            "__call__": lambda self, text, return_tensors=None: {},
            "decode": lambda self, ids, skip_special_tokens=True: "hi there",
        },
    )()

    used = {}
    def fake_load_model(path):
        used["path"] = path
        return dummy_model, dummy_tokenizer

    monkeypatch.setattr(inanna_ai.model, "load_model", fake_load_model)

    inputs = iter(["hello", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    argv_backup = sys.argv.copy()
    sys.argv = ["INANNA_AI.py", "chat"]
    try:
        inanna_ai.main()
    finally:
        sys.argv = argv_backup

    out = capsys.readouterr().out
    assert "Quantum Ritual Boot" in out
    assert "hi there" in out
    assert used.get("path") == inanna_ai.MODEL_PATH


def test_chat_model_dir_option(monkeypatch):
    dummy_model = type("M", (), {"generate": lambda self, **kw: [[0, 1]]})()
    dummy_tokenizer = type(
        "T",
        (),
        {
            "__call__": lambda self, text, return_tensors=None: {},
            "decode": lambda self, ids, skip_special_tokens=True: "hi",
        },
    )()

    seen = {}

    def fake_load_model(path):
        seen["path"] = path
        return dummy_model, dummy_tokenizer

    monkeypatch.setattr(inanna_ai.model, "load_model", fake_load_model)
    inputs = iter(["exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    argv_backup = sys.argv.copy()
    sys.argv = ["INANNA_AI.py", "chat", "--model-dir", "custom"]
    try:
        inanna_ai.main()
    finally:
        sys.argv = argv_backup

    assert seen.get("path") == Path("custom")


def test_status_option_outputs_state(monkeypatch, capsys):
    monkeypatch.setattr(inanna_ai.emotional_state, "get_last_emotion", lambda: "joy")
    monkeypatch.setattr(inanna_ai.emotion_registry, "get_current_layer", lambda: "rubedo_layer")

    argv_backup = sys.argv.copy()
    sys.argv = ["INANNA_AI.py", "--status"]
    try:
        inanna_ai.main()
    finally:
        sys.argv = argv_backup

    out = capsys.readouterr().out
    assert "joy" in out
    assert "rubedo_layer" in out


def test_voice_loop_gates(monkeypatch):
    import types, sys
    sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
    numpy_mod = types.ModuleType("numpy")
    numpy_mod.ndarray = object
    sys.modules.setdefault("numpy", numpy_mod)
    sys.modules.setdefault("librosa", types.ModuleType("librosa"))
    wavfile_mod = types.ModuleType("wavfile")
    wavfile_mod.write = lambda *a, **k: None
    io_mod = types.ModuleType("io")
    io_mod.wavfile = wavfile_mod
    scipy_mod = types.ModuleType("scipy")
    scipy_mod.io = io_mod
    sys.modules.setdefault("scipy", scipy_mod)
    sys.modules.setdefault("scipy.io", io_mod)
    sys.modules.setdefault("scipy.io.wavfile", wavfile_mod)
    cryptography_mod = types.ModuleType("cryptography")
    hazmat_mod = types.ModuleType("hazmat")
    primitives = types.ModuleType("primitives")
    hashes_mod = types.ModuleType("hashes")
    primitives.hashes = hashes_mod
    asym_mod = types.ModuleType("asymmetric")
    padding_mod = types.ModuleType("padding")
    asym_mod.padding = padding_mod
    asym_mod.rsa = lambda *a, **k: None
    primitives.asymmetric = asym_mod
    serialization_mod = types.ModuleType("serialization")
    serialization_mod.load_pem_private_key = lambda *a, **k: None
    serialization_mod.load_pem_public_key = lambda *a, **k: None
    hazmat_mod.primitives = primitives
    cryptography_mod.hazmat = hazmat_mod
    sys.modules.setdefault("cryptography", cryptography_mod)
    sys.modules.setdefault("cryptography.hazmat", hazmat_mod)
    sys.modules.setdefault("cryptography.hazmat.primitives", primitives)
    sys.modules.setdefault("cryptography.hazmat.primitives.hashes", hashes_mod)
    sys.modules.setdefault("cryptography.hazmat.primitives.asymmetric", asym_mod)
    sys.modules.setdefault("cryptography.hazmat.primitives.asymmetric.padding", padding_mod)
    sys.modules.setdefault("cryptography.hazmat.primitives.serialization", serialization_mod)
    from INANNA_AI import main as voice_main

    monkeypatch.setattr(voice_main.utils, "setup_logger", lambda: None)
    monkeypatch.setattr(voice_main.db_storage, "init_db", lambda: None)
    saved = {}
    monkeypatch.setattr(
        voice_main.db_storage,
        "save_interaction",
        lambda t, e, p: saved.update({"transcript": t, "path": p}),
    )

    class DummyEngine:
        def record(self, duration):
            return "a.wav", {"emotion": "calm"}

    monkeypatch.setattr(voice_main.listening_engine, "ListeningEngine", lambda: DummyEngine())
    monkeypatch.setattr(voice_main.stt_whisper, "transcribe_audio", lambda p: "hello")

    class DummyGate:
        def process_inward(self, text):
            saved["inward"] = text
            return ["vec"]

        def process_outward(self, grid):
            saved["grid"] = grid
            return "gate"

    monkeypatch.setattr(voice_main, "GateOrchestrator", lambda: DummyGate())

    class DummyCore:
        def execute(self, vec):
            saved["core"] = vec
            return [1]

    monkeypatch.setattr(voice_main, "RFA7D", lambda: DummyCore())

    class DummyOrch:
        def route(self, t, state, text_modality=True, voice_modality=False, music_modality=False):
            saved["routed"] = t
            return {"text": "reply"}

    monkeypatch.setattr(voice_main, "MoGEOrchestrator", lambda: DummyOrch())

    class DummySpeaker:
        def speak(self, text, emotion):
            saved["spoken"] = text
            saved["emotion"] = emotion
            return "resp.wav"

    monkeypatch.setattr(voice_main.speaking_engine, "SpeakingEngine", lambda: DummySpeaker())

    voice_main.main([])

    assert saved["spoken"] == "reply gate"
    assert saved["path"] == "resp.wav"


def test_personality_flag_initializes_layer(monkeypatch):
    import sys, types
    sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
    sys.modules["soundfile"].write = lambda *a, **k: None
    sys.modules.setdefault("numpy", types.ModuleType("numpy"))
    sys.modules["numpy"].random = types.SimpleNamespace(rand=lambda *a, **k: 0)
    sys.modules["numpy"].int16 = "int16"
    sys.modules.setdefault("librosa", types.ModuleType("librosa"))
    sys.modules["librosa"].load = lambda *a, **k: ([], 0)
    wavfile_mod = types.ModuleType("wavfile")
    wavfile_mod.write = lambda *a, **k: None
    io_mod = types.ModuleType("io")
    io_mod.wavfile = wavfile_mod
    scipy_mod = types.ModuleType("scipy")
    scipy_mod.io = io_mod
    sys.modules.setdefault("scipy", scipy_mod)
    sys.modules.setdefault("scipy.io", io_mod)
    sys.modules.setdefault("scipy.io.wavfile", wavfile_mod)
    sys.modules.setdefault("SPIRAL_OS.qnl_engine", types.ModuleType("qnl_engine"))
    gates_mod = types.ModuleType("gates")
    gates_mod.sign_blob = lambda *a, **k: b""
    gates_mod.verify_blob = lambda *a, **k: True
    sys.modules.setdefault("INANNA_AI.gates", gates_mod)
    cryptography_mod = types.ModuleType("cryptography")
    hazmat_mod = types.ModuleType("hazmat")
    primitives = types.ModuleType("primitives")
    hashes_mod = types.ModuleType("hashes")
    hashes_mod.Hash = lambda *a, **k: None
    primitives.hashes = hashes_mod
    asym_mod = types.ModuleType("asymmetric")
    padding_mod = types.ModuleType("padding")
    asym_mod.padding = padding_mod
    primitives.asymmetric = asym_mod
    hazmat_mod.primitives = primitives
    cryptography_mod.hazmat = hazmat_mod
    sys.modules.setdefault("cryptography", cryptography_mod)
    sys.modules.setdefault("cryptography.hazmat", hazmat_mod)
    sys.modules.setdefault("cryptography.hazmat.primitives", primitives)
    sys.modules.setdefault("cryptography.hazmat.primitives.hashes", hashes_mod)
    sys.modules.setdefault("cryptography.hazmat.primitives.asymmetric", asym_mod)
    sys.modules.setdefault("cryptography.hazmat.primitives.asymmetric.padding", padding_mod)

    from INANNA_AI import main as voice_main

    monkeypatch.setattr(voice_main.utils, "setup_logger", lambda: None)
    monkeypatch.setattr(voice_main.db_storage, "save_interaction", lambda *a, **k: None)
    monkeypatch.setattr(voice_main.db_storage, "init_db", lambda: None)

    class DummyEngine:
        def record(self, duration):
            return "a.wav", {"emotion": "calm"}

    monkeypatch.setattr(voice_main.listening_engine, "ListeningEngine", lambda: DummyEngine())
    monkeypatch.setattr(voice_main.stt_whisper, "transcribe_audio", lambda p: "hi")

    class DummyGate:
        def process_inward(self, text):
            return ["vec"]

        def process_outward(self, grid):
            return "gate"

    monkeypatch.setattr(voice_main, "GateOrchestrator", lambda: DummyGate())
    monkeypatch.setattr(voice_main, "RFA7D", lambda: type("C", (), {"execute": lambda self, v: [1], "grid": type("G", (), {"size": 1})()})())

    created = {}

    class DummyLayer:
        pass

    def make_layer():
        created["layer"] = True
        return DummyLayer()

    monkeypatch.setattr(voice_main, "REGISTRY", {"albedo": make_layer})

    class DummyOrch:
        def __init__(self, *, albedo_layer=None):
            created["albedo"] = albedo_layer

        def route(self, *a, **k):
            return {"text": "reply"}

    monkeypatch.setattr(voice_main, "MoGEOrchestrator", DummyOrch)
    monkeypatch.setattr(voice_main.speaking_engine, "SpeakingEngine", lambda: type("S", (), {"speak": lambda self, t, e: "v.wav"})())

    voice_main.main(["--duration", "0", "--personality", "albedo"])

    assert created.get("layer")
    assert isinstance(created.get("albedo"), DummyLayer)
