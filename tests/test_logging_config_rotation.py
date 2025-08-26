import hashlib
import logging
import logging.config
from pathlib import Path

import yaml


def test_logging_rotation(tmp_path):
    config_path = Path(__file__).resolve().parents[1] / "logging_config.yaml"
    with config_path.open("r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    log_file = tmp_path / "INANNA_AI.log"
    config["handlers"]["file"]["filename"] = str(log_file)
    config["handlers"]["file"]["maxBytes"] = 200
    config["handlers"]["file"]["backupCount"] = 2
    audio_file = tmp_path / "audio.log"
    config["handlers"]["audio"]["filename"] = str(audio_file)
    logging.config.dictConfig(config)

    logger = logging.getLogger("rotation-test")
    logger.info("A" * 120)
    for handler in logging.getLogger().handlers:
        handler.flush()

    initial_data = log_file.read_bytes()
    initial_checksum = hashlib.sha256(initial_data).hexdigest()

    logger.info("B" * 120)
    for handler in logging.getLogger().handlers:
        handler.flush()

    rolled_file = log_file.with_name("INANNA_AI.log.1")
    assert rolled_file.exists()
    assert rolled_file.stat().st_size <= 200
    rolled_checksum = hashlib.sha256(rolled_file.read_bytes()).hexdigest()
    assert rolled_checksum == initial_checksum
