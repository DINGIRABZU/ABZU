# Alpha Gate Run 20250927T235425Z

- rm -rf dist/ (exit 0)
- python -m build --wheel (exit 1)
- bash scripts/check_requirements.sh (exit 1)
- python scripts/verify_self_healing.py --max-quarantine-hours 24 --max-cycle-hours 24 (exit 1)
- python scripts/health_check_connectors.py (exit 1)
- pytest Stage A suite (exit 4)
- pytest telemetry follow-up (exit 4)
- python scripts/razar_chaos_drill.py --dry-run (exit 1)
