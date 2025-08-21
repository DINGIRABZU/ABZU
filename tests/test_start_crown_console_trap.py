import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_launch_servants_failure_cleans_temp_file(tmp_path):
    tmp_dir = tmp_path
    # copy start_crown_console.sh
    start_script = tmp_dir / "start_crown_console.sh"
    start_script.write_text((ROOT / "start_crown_console.sh").read_text())
    start_script.chmod(0o755)

    # stub crown_model_launcher.sh
    launcher = tmp_dir / "crown_model_launcher.sh"
    launcher.write_text("#!/bin/bash\nexit 0\n")
    launcher.chmod(0o755)

    # stub failing launch_servants.sh
    servants = tmp_dir / "launch_servants.sh"
    servants.write_text("#!/bin/bash\nexit 1\n")
    servants.chmod(0o755)

    # stub scripts/check_prereqs.sh
    scripts_dir = tmp_dir / "scripts"
    scripts_dir.mkdir()
    check = scripts_dir / "check_prereqs.sh"
    check.write_text("#!/bin/bash\nexit 0\n")
    check.chmod(0o755)

    # minimal secrets.env
    (tmp_dir / "secrets.env").write_text("GLM_API_URL=http://localhost:8000\n")

    # stub mktemp to known path
    bin_dir = tmp_dir / "bin"
    bin_dir.mkdir()
    temp_file = tmp_dir / "servant_endpoints.tmp"
    mktemp_stub = bin_dir / "mktemp"
    mktemp_stub.write_text(f"#!/bin/bash\n touch '{temp_file}'\n printf '%s\\n' '{temp_file}'\n")
    mktemp_stub.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"

    result = subprocess.run(["bash", str(start_script)], cwd=tmp_dir, env=env)

    assert result.returncode != 0
    assert not temp_file.exists()
