#!/usr/bin/env bash
# Orchestrate the Alpha v0.1 readiness gate: packaging, health checks, and tests.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs/alpha_gate"

SKIP_BUILD=0
SKIP_HEALTH=0
SKIP_TESTS=0
RUN_CONNECTOR_CHECK=0
PYTEST_EXTRA=()

usage() {
    cat <<'USAGE'
Usage: scripts/run_alpha_gate.sh [options] [-- <pytest args>]

Options:
  --skip-build         Skip the packaging phase.
  --skip-health        Skip mandatory health checks.
  --skip-tests         Skip acceptance test execution.
  --check-connectors   Run connector heartbeat checks during the health phase.
  --pytest-args ARGS   Extra arguments passed to pytest (may be repeated).
  -h, --help           Show this help message.

Arguments after "--" are forwarded to pytest.
USAGE
}

timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

log_entry() {
    local log_file="$1"
    shift
    local message="$*"
    local entry
    entry="[$(timestamp)] $message"
    echo "$entry"
    echo "$entry" >>"$log_file"
}

parse_args() {
    while (($#)); do
        case "$1" in
            --skip-build)
                SKIP_BUILD=1
                shift
                ;;
            --skip-health)
                SKIP_HEALTH=1
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=1
                shift
                ;;
            --check-connectors)
                RUN_CONNECTOR_CHECK=1
                shift
                ;;
            --pytest-args)
                shift
                if (($# == 0)); then
                    echo "--pytest-args requires a value" >&2
                    exit 1
                fi
                PYTEST_EXTRA+=("$1")
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            --)
                shift
                while (($#)); do
                    PYTEST_EXTRA+=("$1")
                    shift
                done
                ;;
            *)
                echo "Unknown option: $1" >&2
                usage >&2
                exit 1
                ;;
        esac
    done
}

ensure_log_dir() {
    mkdir -p "$LOG_DIR"
}

run_build() {
    local log_file="$LOG_DIR/build.log"
    : >"$log_file"
    log_entry "$log_file" "Starting packaging phase"
    log_entry "$log_file" "Cleaning dist/ directory"
    rm -rf "$ROOT_DIR/dist"
    log_entry "$log_file" "Building wheel via python -m build --wheel"
    (
        cd "$ROOT_DIR"
        python -m build --wheel
    ) 2>&1 | tee -a "$log_file"
    log_entry "$log_file" "Packaging phase completed"
}

run_health_checks() {
    local log_file="$LOG_DIR/health_checks.log"
    : >"$log_file"
    log_entry "$log_file" "Starting health checks"
    log_entry "$log_file" "Running scripts/check_requirements.sh"
    "$SCRIPT_DIR/check_requirements.sh" 2>&1 | tee -a "$log_file"
    log_entry "$log_file" "Running verify_self_healing.py"
    (
        cd "$ROOT_DIR"
        python scripts/verify_self_healing.py --max-quarantine-hours 24 --max-cycle-hours 24
    ) 2>&1 | tee -a "$log_file"
    if ((RUN_CONNECTOR_CHECK == 1)); then
        log_entry "$log_file" "Running connector health sweep"
        (
            cd "$ROOT_DIR"
            python scripts/health_check_connectors.py
        ) 2>&1 | tee -a "$log_file"
    else
        log_entry "$log_file" "Skipping connector sweep (enable with --check-connectors)"
    fi
    log_entry "$log_file" "Health checks completed"
}

run_tests() {
    local log_file="$LOG_DIR/tests.log"
    : >"$log_file"
    log_entry "$log_file" "Starting acceptance tests"
    local pytest_args=(
        tests/test_start_spiral_os.py
        tests/test_spiral_os.py
        tests/integration/test_razar_failover.py
    )
    if ((${#PYTEST_EXTRA[@]} > 0)); then
        pytest_args+=("${PYTEST_EXTRA[@]}")
    fi
    log_entry "$log_file" "Running pytest ${pytest_args[*]}"
    (
        cd "$ROOT_DIR"
        pytest "${pytest_args[@]}"
    ) 2>&1 | tee -a "$log_file"
    log_entry "$log_file" "Acceptance tests completed"
}

main() {
    parse_args "$@"
    ensure_log_dir

    if ((SKIP_BUILD == 0)); then
        run_build
    else
        echo "[$(timestamp)] Skipping packaging phase"
    fi

    if ((SKIP_HEALTH == 0)); then
        run_health_checks
    else
        echo "[$(timestamp)] Skipping health checks"
    fi

    if ((SKIP_TESTS == 0)); then
        run_tests
    else
        echo "[$(timestamp)] Skipping acceptance tests"
    fi

    echo "[$(timestamp)] Alpha gate completed"
}

main "$@"
