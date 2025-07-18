import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub heavy optional dependencies before importing the module
sys.modules.setdefault("opensmile", types.ModuleType("opensmile"))
sys.modules.setdefault("EmotiVoice", types.ModuleType("EmotiVoice"))
sys.modules.setdefault("librosa", types.ModuleType("librosa"))
sys.modules.setdefault("soundfile", types.ModuleType("soundfile"))
sys.modules.setdefault("openvoice", types.ModuleType("openvoice"))
sys.modules.setdefault("gtts", types.ModuleType("gtts"))

from SPIRAL_OS import symbolic_parser


def test_parse_intent_memory(monkeypatch):
    called = {}

    def dummy_search(query, top_k=3, dirs=None, model_name="all-MiniLM-L6-v2"):
        called['query'] = query
        return [("p", "s")]

    monkeypatch.setattr(symbolic_parser.corpus_memory, "search_corpus", dummy_search)

    result = symbolic_parser.parse_intent({"text": "summon memory"})

    assert called['query']
    assert result == [[("p", "s")]]



def test_parse_intent_voice(monkeypatch):
    calls = {}

    def fake_speak(text: str, tone: str):
        calls['args'] = (text, tone)
        return 'v.wav'

    monkeypatch.setattr(symbolic_parser.voice_layer_albedo, 'speak', fake_speak)
    result = symbolic_parser.parse_intent({'text': 'weave sound', 'tone': 'joy'})
    assert result == ['v.wav']
    assert calls['args'] == ('weave sound', 'joy')


def test_parse_intent_placeholder(monkeypatch):
    called = {}

    def fake_open(data):
        called['data'] = data
        return 'ok'

    monkeypatch.setitem(symbolic_parser._ACTIONS, 'gateway.open', fake_open)
    result = symbolic_parser.parse_intent({'text': 'open portal'})
    assert result == ['ok']
    assert called['data']['text'] == 'open portal'


def test_route_intent_memory(monkeypatch):
    called = {}

    def dummy_search(query, top_k=3):
        called['query'] = query
        return ['hit']

    monkeypatch.setattr(symbolic_parser.corpus_memory, 'search_corpus', dummy_search)
    intent = {'intent': 'invoke remembrance', 'action': 'memory.recall', 'text': 'alpha'}
    result = symbolic_parser.route_intent(intent)
    assert result == ['hit']
    assert called['query'] == 'alpha'


def test_route_intent_voice(monkeypatch):
    calls = {}

    def fake_speak(text: str, tone: str):
        calls['args'] = (text, tone)
        return 'p.wav'

    monkeypatch.setattr(symbolic_parser.voice_layer_albedo, 'speak', fake_speak)
    intent = {'intent': 'play', 'action': 'voice_layer.play', 'text': 'beta', 'tone': 'joy'}
    result = symbolic_parser.route_intent(intent)
    assert result == 'p.wav'
    assert calls['args'] == ('beta', 'joy')


def test_route_intent_music(monkeypatch):
    calls = {}

    def fake_play(seq: str, emo: str):
        calls['args'] = (seq, emo)
        return 'x.wav'

    monkeypatch.setattr(symbolic_parser.seven_dimensional_music, 'play_sequence', fake_play)
    intent = {'intent': 'play', 'action': 'music.play_sequence', 'text': 'notes', 'tone': 'calm'}
    result = symbolic_parser.route_intent(intent)
    assert result == 'x.wav'
    assert calls['args'] == ('notes', 'calm')


def test_route_intent_ritual(monkeypatch):
    called = {}

    def fake_vault(data):
        called['data'] = data
        return 'ok'

    monkeypatch.setattr(symbolic_parser.ritual, 'vault_open', fake_vault)
    intent = {'intent': 'open vault', 'action': 'ritual.vault_open', 'text': 'secret'}
    result = symbolic_parser.route_intent(intent)
    assert result == 'ok'
    assert called['data']['text'] == 'secret'
