# Failure Inventory

Test run: `pytest -vv --cov` on 2025-08-31.

## RAZAR
- [tests/test_quarantine_manager.py](../../tests/test_quarantine_manager.py) – import file mismatch caused by duplicate module names.

## Crown
- [tests/test_dashboard_app.py](../../tests/test_dashboard_app.py) – Plotly theme configuration uses a string where a numeric array is expected, leading to `AttributeError: 'str' object has no attribute 'dtype'`.
- [tests/test_dashboard_qnl_mixer.py](../../tests/test_dashboard_qnl_mixer.py) – same Plotly configuration issue as above.

## Memory layers
- [tests/test_vector_memory.py](../../tests/test_vector_memory.py) – import file mismatch due to duplicate test module names.

## Operator API
- No failures after installing `python-multipart`.

## Other components
- [tests/test_emotion_classifier.py](../../tests/test_emotion_classifier.py) – scikit-learn raises `AttributeError` referencing `RandomState`.
- [tests/test_voice_cloner_cli.py](../../tests/test_voice_cloner_cli.py) – `ImportError` for `load_config` in `core` module.

See [logs/test_report.txt](../../logs/test_report.txt) for full pytest output.

