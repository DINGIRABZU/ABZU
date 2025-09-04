# Chakra Healing

The chakra healing suite provides recovery scripts invoked by resource guardians when Chakracon metrics exceed safe thresholds.

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/chakra_healing/root_restore_network.sh` | Restart network interface or reduce disk I/O |
| `scripts/chakra_healing/sacral_gpu_recover.py` | Reset GPU VRAM or pause GPU tasks |
| `scripts/chakra_healing/solar_cpu_throttle.py` | Cap runaway CPU processes via cgroups |
| `scripts/chakra_healing/heart_memory_repair.py` | Compact or purge memory layers |
| `scripts/chakra_healing/throat_api_stabilize.sh` | Adjust rate limits or restart gateway services |
| `scripts/chakra_healing/third_eye_inference_flush.py` | Clear model queue and hot-reload model |
| `scripts/chakra_healing/crown_full_restart.sh` | Orchestrate system reboot and operator notification |

## Version History

| Version | Date | Notes |
| --- | --- | --- |
| Unreleased | 2025-09-?? | Initial description of chakra healing scripts. |
