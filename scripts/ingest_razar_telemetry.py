"""Aggregate RAZAR invocation telemetry into ledger-friendly snapshots."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, List

import pandas as pd

LOG_PATH = Path("logs/razar_ai_invocations.json")
OUTPUT_DIR = Path("monitoring") / "self_healing_ledger"
JSON_OUTPUT = OUTPUT_DIR / "razar_agent_trends.json"
PARQUET_OUTPUT = OUTPUT_DIR / "razar_agent_trends.parquet"

REQUIRED_DTYPES = {
    "date": "datetime64[ns, UTC]",
    "agent": "string",
    "component": "string",
    "attempts": "int64",
    "successes": "int64",
    "failures": "int64",
    "success_rate": "float64",
    "first_timestamp": "datetime64[ns, UTC]",
    "last_timestamp": "datetime64[ns, UTC]",
}


@dataclass(slots=True)
class InvocationRecord:
    """Normalized view of a single AI invocation."""

    timestamp: datetime
    component: str
    agent: str
    success: bool
    attempt: int | None

    @property
    def date(self) -> datetime:
        return self.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)


def _parse_timestamp(value: object, iso_value: object) -> datetime | None:
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (OverflowError, ValueError):
            return None
    if isinstance(value, str):
        try:
            return datetime.fromtimestamp(float(value), tz=UTC)
        except (OverflowError, ValueError):
            pass
    if isinstance(iso_value, str):
        try:
            cleaned = iso_value.replace("Z", "+00:00")
            return datetime.fromisoformat(cleaned).astimezone(UTC)
        except ValueError:
            return None
    return None


def _coerce_attempt(raw: object) -> int | None:
    try:
        if raw is None:
            return None
        attempt = int(raw)
        return attempt if attempt >= 0 else None
    except (TypeError, ValueError):
        return None


def _coerce_success(entry: dict[str, object]) -> bool | None:
    status = entry.get("status")
    patched = entry.get("patched")
    if isinstance(patched, bool):
        success = patched
    elif isinstance(status, str):
        lowered = status.lower()
        if lowered in {"success", "succeeded", "ok", "recovered"}:
            success = True
        elif lowered in {"failure", "failed", "error"}:
            success = False
        else:
            success = None
    else:
        success = None
    return success


def _iter_json_objects(path: Path) -> Iterable[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    stripped = text.lstrip()
    if not stripped:
        return []
    if stripped.startswith("["):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []
    objects: list[dict[str, object]] = []
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            objects.append(data)
    return objects


def load_invocations(log_path: Path = LOG_PATH) -> list[InvocationRecord]:
    """Parse invocation JSON lines into normalized records."""

    if not log_path.exists():
        return []

    records: list[InvocationRecord] = []
    for entry in _iter_json_objects(log_path):
        timestamp = _parse_timestamp(entry.get("timestamp"), entry.get("timestamp_iso"))
        if not timestamp:
            continue
        success = _coerce_success(entry)
        if success is None:
            continue
        component = str(entry.get("component") or "unknown")
        agent = str(
            entry.get("agent")
            or entry.get("agent_original")
            or entry.get("delegate")
            or "unknown"
        )
        attempt = _coerce_attempt(entry.get("attempt"))
        records.append(
            InvocationRecord(
                timestamp=timestamp,
                component=component,
                agent=agent,
                success=bool(success),
                attempt=attempt,
            )
        )
    return records


def _empty_trend_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {col: pd.Series(dtype=dtype) for col, dtype in REQUIRED_DTYPES.items()}
    )


def aggregate_agent_trends(records: Iterable[InvocationRecord]) -> pd.DataFrame:
    """Aggregate invocation records into per-day success metrics."""

    data = list(records)
    if not data:
        return _empty_trend_frame()

    df = pd.DataFrame(
        {
            "timestamp": [item.timestamp for item in data],
            "component": [item.component for item in data],
            "agent": [item.agent for item in data],
            "success": [item.success for item in data],
        }
    )
    df["date"] = df["timestamp"].dt.floor("D")

    grouped = (
        df.groupby(["date", "agent", "component"], as_index=False)
        .agg(
            attempts=("success", "size"),
            successes=("success", "sum"),
            first_timestamp=("timestamp", "min"),
            last_timestamp=("timestamp", "max"),
        )
        .sort_values(["date", "agent", "component"])  # Stable order for reproducibility
    )

    grouped["failures"] = grouped["attempts"] - grouped["successes"]
    grouped["success_rate"] = grouped["successes"].where(
        grouped["attempts"] > 0, 0
    ) / grouped["attempts"].where(grouped["attempts"] > 0, 1)
    grouped["success_rate"] = grouped["success_rate"].round(4)

    trend = grouped[
        [
            "date",
            "agent",
            "component",
            "attempts",
            "successes",
            "failures",
            "success_rate",
            "first_timestamp",
            "last_timestamp",
        ]
    ].reset_index(drop=True)
    return trend.astype(REQUIRED_DTYPES)


def _prepare_for_serialization(df: pd.DataFrame) -> List[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in df.to_dict(orient="records"):
        record = dict(row)
        for field in ("date", "first_timestamp", "last_timestamp"):
            value = record.get(field)
            if isinstance(value, pd.Timestamp):
                if value.tzinfo is None:
                    value = value.tz_localize(UTC)
                else:
                    value = value.tz_convert(UTC)
                record[field] = value.isoformat().replace("+00:00", "Z")
            elif pd.isna(value):
                record[field] = None
        records.append(record)
    return records


def write_outputs(df: pd.DataFrame, output_dir: Path = OUTPUT_DIR) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_payload = _prepare_for_serialization(df)
    JSON_OUTPUT.relative_to(OUTPUT_DIR)
    json_path = output_dir / JSON_OUTPUT.name
    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    parquet_path = output_dir / PARQUET_OUTPUT.name
    if df.empty:
        empty = _empty_trend_frame()
        empty.to_parquet(parquet_path, index=False)
    else:
        df.to_parquet(parquet_path, index=False)


def ingest_razar_telemetry(
    log_path: Path = LOG_PATH, output_dir: Path = OUTPUT_DIR
) -> pd.DataFrame:
    """Load invocation telemetry and persist aggregated trends."""

    records = load_invocations(log_path)
    trend = aggregate_agent_trends(records)
    write_outputs(trend, output_dir=output_dir)
    return trend


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log-path",
        type=Path,
        default=LOG_PATH,
        help="Location of razar_ai_invocations.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory where aggregated parquet and JSON outputs are written",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    ingest_razar_telemetry(log_path=args.log_path, output_dir=args.output_dir)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
