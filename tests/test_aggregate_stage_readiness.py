from __future__ import annotations

import json
from pathlib import Path

from scripts import aggregate_stage_readiness as readiness_aggregate
import operator_api
from tests.conftest import allow_test


allow_test(Path(__file__).resolve())


def test_aggregate_stage_readiness_copies_summaries_and_logs(
    tmp_path, monkeypatch
) -> None:
    stage_a_root = tmp_path / "stage_a"
    stage_b_root = tmp_path / "stage_b"
    stage_c_dir = tmp_path / "stage_c"

    stage_a_slug_dir = stage_a_root / "20240101T000000Z-stage_a1_boot_telemetry"
    stage_b_run_dir = stage_b_root / "20240102T000000Z-stage_b1_memory_proof"
    stage_a_slug_dir.mkdir(parents=True, exist_ok=True)
    stage_b_run_dir.mkdir(parents=True, exist_ok=True)

    stage_a_summary_path = stage_a_slug_dir / "summary.json"
    stage_a_stderr = stage_a_slug_dir / "stage_a1_boot_telemetry.stderr.log"
    stage_a_stdout = stage_a_slug_dir / "stage_a1_boot_telemetry.stdout.log"
    stage_a_stderr.write_text("stage-a stderr", encoding="utf-8")
    stage_a_stdout.write_text("stage-a stdout", encoding="utf-8")
    stage_a_summary_path.write_text(
        json.dumps(
            {
                "slug": "A1",
                "status": "success",
                "run_id": "a1-run",
                "completed_at": "2024-01-01T00:05:00Z",
                "log_dir": str(stage_a_slug_dir),
                "stdout_path": str(stage_a_stdout),
                "stderr_path": str(stage_a_stderr),
                "stderr_tail": ["tail"],
            }
        ),
        encoding="utf-8",
    )

    stage_b_summary_path = stage_b_run_dir / "summary.json"
    stage_b_stderr = stage_b_run_dir / "stage_b1_memory_proof.stderr.log"
    stage_b_stdout = stage_b_run_dir / "stage_b1_memory_proof.stdout.log"
    stage_b_stderr.write_text("stage-b stderr", encoding="utf-8")
    stage_b_stdout.write_text("stage-b stdout", encoding="utf-8")
    stage_b_summary_path.write_text(
        json.dumps(
            {
                "stage": "stage_b1_memory_proof",
                "status": "success",
                "run_id": "b1-run",
                "completed_at": "2024-01-02T00:05:00Z",
                "log_dir": str(stage_b_run_dir),
                "stdout_path": str(stage_b_stdout),
                "stderr_path": str(stage_b_stderr),
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(readiness_aggregate, "STAGE_A_ROOT", stage_a_root)
    monkeypatch.setattr(readiness_aggregate, "STAGE_B_ROOT", stage_b_root)

    bundle_path, summary_payload = readiness_aggregate.aggregate(stage_c_dir)

    assert bundle_path.exists()
    stage_a_slugs = summary_payload["stage_a"]["slugs"]
    stage_a_entry = stage_a_slugs["A1"]
    stage_b_entry = summary_payload["stage_b"]

    copied_stage_a_summary = Path(stage_a_entry["summary_path"])
    assert copied_stage_a_summary.exists()
    assert copied_stage_a_summary.parent == stage_c_dir
    assert Path(stage_a_entry["source_summary_path"]) == stage_a_summary_path

    for artifact_path in stage_a_entry["artifacts"]:
        copied_artifact = Path(artifact_path)
        assert copied_artifact.exists()
        assert copied_artifact.parent == stage_c_dir
    assert {Path(p) for p in stage_a_entry["source_artifacts"]} == {
        stage_a_stdout,
        stage_a_stderr,
    }

    copied_stage_b_summary = Path(stage_b_entry["summary_path"])
    assert copied_stage_b_summary.exists()
    assert copied_stage_b_summary.parent == stage_c_dir
    assert Path(stage_b_entry["source_summary_path"]) == stage_b_summary_path

    assert stage_b_entry["artifacts"]
    assert {Path(p) for p in stage_b_entry["source_artifacts"]} == {
        stage_b_stdout,
        stage_b_stderr,
    }
    for artifact_path in stage_b_entry["artifacts"]:
        copied_artifact = Path(artifact_path)
        assert copied_artifact.exists()
        assert copied_artifact.parent == stage_c_dir

    payload: dict[str, object] = {}
    metrics = operator_api._stage_c3_metrics("", "", stage_c_dir, payload)

    artifacts = payload["artifacts"]
    assert isinstance(artifacts, dict)
    stage_a_summary_artifact = Path(artifacts["stage_a_a1_summary"])  # type: ignore[index]
    assert stage_a_summary_artifact == copied_stage_a_summary
    stage_b_summary_artifact = Path(artifacts["stage_b_summary"])  # type: ignore[index]
    assert stage_b_summary_artifact == copied_stage_b_summary

    stage_a_artifact_values = [
        Path(path)
        for key, path in artifacts.items()
        if key.startswith("stage_a_a1_artifact")
    ]
    assert all(path.parent == stage_c_dir for path in stage_a_artifact_values)

    stage_b_artifact_values = [
        Path(path)
        for key, path in artifacts.items()
        if key.startswith("stage_b_artifact")
    ]
    assert all(path.parent == stage_c_dir for path in stage_b_artifact_values)

    assert metrics["stage_a"]["slugs"]["A1"]["summary_path"] == str(
        copied_stage_a_summary
    )
    assert metrics["stage_b"]["summary_path"] == str(copied_stage_b_summary)
