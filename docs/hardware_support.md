# Hardware Support

## Stage A Runner Profile

| Component | Specification |
| --- | --- |
| Chassis | Supermicro SYS-510P-ML with redundant 750 W PSUs |
| CPU | Intel Xeon Silver 4410Y (12 cores / 24 threads, 2.0 GHz base, 3.5 GHz turbo) |
| Memory | 128 GB DDR5-4800 ECC (4 × 32 GB) |
| Storage | 2 × 1 TB NVMe (RAID1) for OS, 1 × 2 TB NVMe scratch volume |
| Networking | Dual-port 10 GbE (SFP+) uplinks with bonded LACP |
| Accelerator | None (Stage A runs in CPU-only mode) |

### Runtime Flags

- CUDA available: False
- ROCm available: False
- Intel GPU available: False
- Selected device: cpu

## Required Firmware and BIOS Settings

- BIOS version 2.5c with microcode package `14.0.45`.
- Enable `VT-d`, `SR-IOV`, and `Turbo Boost` while keeping `C-States` on `Auto` to
  reduce boot jitter.
- Update the BMC to 01.14.12 for correct power telemetry streaming into the
  Node Exporter panels.
- Stage A runners boot from UEFI with Secure Boot disabled to allow the
  telemetry sidecar to attach early in the initramfs.

## Exporter Configuration

- Install `node_exporter` with the textfile collector pointed at
  `/var/lib/node_exporter/textfile_collector/` and grant the CI user write
  access.
- Symlink `monitoring/boot_metrics.prom` into the collector directory after each
  gate run so Prometheus scrapes the first-attempt success, retry totals, and
  boot duration gauges.
- Add the following scrape job to `prometheus.yml` on the runner:

  ```yaml
  - job_name: "stage-a-boot-metrics"
    static_configs:
      - targets: ["localhost:9100"]
        labels:
          runner: "stage-a"
    params:
      collect[]:
        - textfile
  ```

- Include `monitoring/grafana-dashboard.json` in the Grafana provisioning
  config so the Boot Ops board automatically surfaces the new gauges alongside
  the Alpha gate summaries.
