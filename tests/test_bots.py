import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tools.bot_telegram as bot_telegram
import tools.bot_discord as bot_discord


def test_send_glm_command(monkeypatch):
    called = {}

    def fake_post(url, json, timeout):
        called['url'] = url
        called['json'] = json

        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {'result': 'ok'}

        return Resp()

    monkeypatch.setattr(bot_telegram, 'requests', type('R', (), {'post': fake_post}))
    out = bot_telegram.send_glm_command('ls')
    assert out == 'ok'
    assert called['url'] == bot_telegram._GLM_URL
    assert called['json'] == {'command': 'ls'}


def test_handle_message(monkeypatch):
    sent = []
    voices = []
    monkeypatch.setattr(bot_telegram, 'send_glm_command', lambda t: 'hi')
    monkeypatch.setattr(bot_telegram, 'send_message', lambda cid, txt: sent.append((cid, txt)))
    monkeypatch.setattr(bot_telegram, 'send_voice', lambda cid, p: voices.append((cid, p)))
    fake_mod = type('M', (), {'speak': lambda t, e: Path('v.wav')})
    monkeypatch.setitem(sys.modules, 'core.expressive_output', fake_mod)

    bot_telegram.handle_message(3, 'cmd')
    assert sent == [(3, 'hi')]
    assert voices == [(3, Path('v.wav'))]


def test_create_client_no_discord(monkeypatch):
    monkeypatch.setattr(bot_discord, 'discord', None)
    with pytest.raises(RuntimeError):
        bot_discord.create_client()
