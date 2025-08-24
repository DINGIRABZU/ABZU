"""Validate training data schema using TensorFlow Data Validation.

This script computes statistics for a CSV dataset and either infers a
schema or validates the data against an existing schema. Outputs are
written under ``data/validation`` by default.
"""

from __future__ import annotations

import argparse
import os

import tensorflow_data_validation as tfdv


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "data",
        help="Path to training data in CSV format.",
    )
    parser.add_argument(
        "--schema",
        default="data/validation/schema.pbtxt",
        help="Path to an existing schema or where to write an inferred one.",
    )
    parser.add_argument(
        "--stats",
        default="data/validation/stats.tfrecord",
        help="Where to write computed statistics.",
    )
    parser.add_argument(
        "--anomalies",
        default="data/validation/anomalies.pbtxt",
        help="Where to write detected anomalies, if any.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(os.path.dirname(args.stats), exist_ok=True)

    stats = tfdv.generate_statistics_from_csv(data_location=args.data)
    tfdv.write_stats_text(stats, args.stats)

    if os.path.exists(args.schema):
        schema = tfdv.load_schema_text(args.schema)
        anomalies = tfdv.validate_statistics(statistics=stats, schema=schema)
        if anomalies.anomaly_info:
            tfdv.write_anomalies_text(anomalies, args.anomalies)
            print(f"Anomalies written to {args.anomalies}")
        else:
            print("No anomalies found.")
    else:
        schema = tfdv.infer_schema(stats)
        tfdv.write_schema_text(schema, args.schema)
        print(f"Schema written to {args.schema}")


if __name__ == "__main__":
    main()
