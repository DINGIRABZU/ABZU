from ai_core.video_pipeline.pipeline import VideoPipeline
from style_engine.style_library import load_style_config


def test_pipeline_selects_pusa_v1():
    config = load_style_config("pusa_v1")
    pipeline = VideoPipeline(config)
    assert pipeline.run("data") == "pusa_v1 processed data"


def test_pipeline_selects_ltx():
    config = load_style_config("ltx")
    pipeline = VideoPipeline(config)
    assert pipeline.run("data") == "ltx processed data"
