import sys
from types import ModuleType
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from INANNA_AI import glm_init, glm_analyze
from INANNA_AI.glm_integration import GLMIntegration


class DummyResponse:
    def __init__(self, data: dict[str, str]):
        self._data = data
        self.text = data.get('summary') or data.get('analysis', '')

    def json(self):
        return self._data

    def raise_for_status(self):
        return None


def test_glm_init_summarize(tmp_path, monkeypatch):
    readme = tmp_path / 'README.md'
    qnl = tmp_path / 'QNL_LANGUAGE'
    qnl.mkdir()
    readme.write_text('hello', encoding='utf-8')
    (qnl / 'a.md').write_text('world', encoding='utf-8')

    out_dir = tmp_path / 'audit_logs'

    monkeypatch.setattr(glm_init, 'ROOT', tmp_path)
    monkeypatch.setattr(glm_init, 'README_FILE', readme)
    monkeypatch.setattr(glm_init, 'QNL_DIR', qnl)
    monkeypatch.setattr(glm_init, 'AUDIT_DIR', out_dir)
    monkeypatch.setattr(glm_init, 'PURPOSE_FILE', out_dir / 'purpose.txt')

    dummy = ModuleType('requests')
    dummy.post = lambda *a, **k: DummyResponse({'summary': 'sum'})
    monkeypatch.setattr(glm_init, 'requests', dummy)

    summary = glm_init.summarize_purpose()
    assert summary == 'sum'
    assert (out_dir / 'purpose.txt').read_text() == 'sum'


def test_glm_analyze_code(tmp_path, monkeypatch):
    code_dir = tmp_path / 'INANNA_AI'
    code_dir.mkdir()
    (code_dir / 'x.py').write_text('print(1)', encoding='utf-8')

    out_dir = tmp_path / 'audit_logs'

    monkeypatch.setattr(glm_analyze, 'ROOT', tmp_path)
    monkeypatch.setattr(glm_analyze, 'CODE_DIR', code_dir)
    monkeypatch.setattr(glm_analyze, 'AUDIT_DIR', out_dir)
    monkeypatch.setattr(glm_analyze, 'ANALYSIS_FILE', out_dir / 'code_analysis.txt')

    dummy = ModuleType('requests')
    dummy.post = lambda *a, **k: DummyResponse({'analysis': 'ok'})
    monkeypatch.setattr(glm_analyze, 'requests', dummy)

    analysis = glm_analyze.analyze_code()
    assert analysis == 'ok'
    assert (out_dir / 'code_analysis.txt').read_text() == 'ok'


def test_env_overrides_endpoint(monkeypatch):
    monkeypatch.setenv('GLM_API_URL', 'http://test/endpoint')
    integration = GLMIntegration()
    assert integration.endpoint == 'http://test/endpoint'


def test_glm_headers(monkeypatch, tmp_path):
    integration = GLMIntegration(api_key='secret')

    readme = tmp_path / 'README.md'
    qnl = tmp_path / 'QNL'
    qnl.mkdir()
    readme.write_text('hi', encoding='utf-8')

    out_dir = tmp_path / 'logs'

    monkeypatch.setattr(glm_init, 'ROOT', tmp_path)
    monkeypatch.setattr(glm_init, 'README_FILE', readme)
    monkeypatch.setattr(glm_init, 'QNL_DIR', qnl)
    monkeypatch.setattr(glm_init, 'AUDIT_DIR', out_dir)
    monkeypatch.setattr(glm_init, 'PURPOSE_FILE', out_dir / 'purpose.txt')

    monkeypatch.setattr(glm_analyze, 'ROOT', tmp_path)
    monkeypatch.setattr(glm_analyze, 'CODE_DIR', qnl)
    monkeypatch.setattr(glm_analyze, 'AUDIT_DIR', out_dir)
    monkeypatch.setattr(glm_analyze, 'ANALYSIS_FILE', out_dir / 'a.txt')

    seen = []
    dummy = ModuleType('requests')

    def post(url, json=None, timeout=10, headers=None):
        seen.append(headers)
        return DummyResponse({'summary': 'x' if 'purpose' in str(out_dir) else 'y'})

    dummy.post = post
    monkeypatch.setattr(glm_init, 'requests', dummy)
    monkeypatch.setattr(glm_analyze, 'requests', dummy)

    glm_init.summarize_purpose(integration)
    glm_analyze.analyze_code(integration)

    assert seen == [{'Authorization': 'Bearer secret'}, {'Authorization': 'Bearer secret'}]


def test_glm_init_error(tmp_path, monkeypatch):
    readme = tmp_path / 'README.md'
    qnl = tmp_path / 'QNL_LANGUAGE'
    qnl.mkdir()
    readme.write_text('hello', encoding='utf-8')
    (qnl / 'a.md').write_text('world', encoding='utf-8')

    out_dir = tmp_path / 'audit_logs'

    monkeypatch.setattr(glm_init, 'ROOT', tmp_path)
    monkeypatch.setattr(glm_init, 'README_FILE', readme)
    monkeypatch.setattr(glm_init, 'QNL_DIR', qnl)
    monkeypatch.setattr(glm_init, 'AUDIT_DIR', out_dir)
    monkeypatch.setattr(glm_init, 'PURPOSE_FILE', out_dir / 'purpose.txt')

    class DummyExc(Exception):
        pass

    class ErrorResp:
        text = 'bad'

        def json(self):
            return {'summary': 'bad'}

        def raise_for_status(self):
            raise DummyExc('fail')

    dummy = ModuleType('requests')
    dummy.RequestException = DummyExc
    dummy.post = lambda *a, **k: ErrorResp()
    monkeypatch.setattr(glm_init, 'requests', dummy)

    with pytest.raises(DummyExc):
        glm_init.summarize_purpose()


def test_glm_analyze_error(tmp_path, monkeypatch):
    code_dir = tmp_path / 'INANNA_AI'
    code_dir.mkdir()
    (code_dir / 'x.py').write_text('print(1)', encoding='utf-8')

    out_dir = tmp_path / 'audit_logs'

    monkeypatch.setattr(glm_analyze, 'ROOT', tmp_path)
    monkeypatch.setattr(glm_analyze, 'CODE_DIR', code_dir)
    monkeypatch.setattr(glm_analyze, 'AUDIT_DIR', out_dir)
    monkeypatch.setattr(glm_analyze, 'ANALYSIS_FILE', out_dir / 'code_analysis.txt')

    class DummyExc(Exception):
        pass

    class ErrorResp:
        text = 'bad'

        def json(self):
            return {'analysis': 'bad'}

        def raise_for_status(self):
            raise DummyExc('fail')

    dummy = ModuleType('requests')
    dummy.RequestException = DummyExc
    dummy.post = lambda *a, **k: ErrorResp()
    monkeypatch.setattr(glm_analyze, 'requests', dummy)

    with pytest.raises(DummyExc):
        glm_analyze.analyze_code()
