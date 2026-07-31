---
name: laptop-hardware-diagnostics
description: >-
  Systematic hardware diagnosis for slow Linux laptops.
version: 1.0.0
bump: 2026-07-30 — initial creation from ThinkPad T14 Gen 1 real-time diagnosis
triggers:
  - "El equipo está lento / va lento / se siente lento"
  - "Revisa el estado del disco / hardware"
  - "CPU stuck at low frequency"
  - "Laptop feels slow after boot"
  - "Revisa el equipo / haz un diagnóstico"
  - "CPU no pasa de 800 MHz"
  - "Turbo boost no funciona"
  - "System sluggish / performance issues"
---

# Laptop Hardware Diagnostics

## Overview

When a user reports a slow system, systematically check four layers before
touching software: **CPU**, **memory**, **storage**, and **boot**.

The single most common cause of perceived slowness on modern Linux laptops is
the CPU being locked at minimum frequency — and it's almost never just the
governor.

## Phase 1: CPU Diagnosis — The Triad Check

Collect ALL THREE metrics in parallel:

```bash
# 1. Governor (software policy)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# 2. Turbo boost (firmware/hardware flag — double negative: 0 = ON, 1 = OFF)
cat /sys/devices/system/cpu/intel_pstate/no_turbo

# 3. Max frequency cap (hardware limit)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq

# — and the actual frequencies at this moment —
grep "MHz" /proc/cpuinfo
```

### The Three Limiter Diagnosis

| Condition | Symptom | Fix |
|-----------|---------|-----|
| `governor=powersave` | All cores at 400-800 MHz | Switch to `performance` |
| `no_turbo=1` | Cores stuck below base freq (e.g. 800 MHz on i7-10510U) | `echo 0 > .../no_turbo` |
| `scaling_max_freq=800000` | Hard cap even at 100% load | Set to CPU's max turbo freq |
| Multiple limiters active | Cumulative performance loss | Fix all three |

### Critical: Also Check Power Source

```bash
cat /sys/class/power_supply/AC*/online   # 1 = plugged in, 0 = on battery
```

On many laptops (ThinkPad, Dell), the firmware hard-disables turbo when on
battery. No software fix can override this — the user must plug in AC power.

### Phase 1b: Quick CPU Health

```bash
lscpu | grep -E "Model name|Core|Thread|CPU MHz"
uptime    # load average
```

## Phase 2: Storage Health

### NVMe Health Check

```bash
sudo smartctl -a /dev/nvme0n1 2>/dev/null | grep -iE \
  "SMART|Temperature|Percentage Used|Media and Data|Error Information|Power On Hours"
```

### Key Metrics

| Metric | Good | Warning | Bad |
|--------|------|---------|-----|
| SMART Status | PASSED | — | FAILED |
| Temperature | 25-55°C | 55-75°C | >82°C |
| Available Spare | >50% | 10-50% | <10% |
| Percentage Used | <20% | 20-50% | >50% |
| Media Errors | 0 | 1-10 | >10 |
| Unsafe Shutdowns | <5% of power cycles | 5-15% | >15% |

### Disk Space

```bash
df -h /
du -sh /home/* 2>/dev/null | sort -rh | head -5
```

If root partition >85% full, performance degrades significantly on NVMe.

## Phase 3: Memory & Swap

```bash
free -h
swapon --show
zramctl 2>/dev/null || echo "no zram"
cat /proc/sys/vm/swappiness
```

### Signs of memory pressure
- swap usage > 0 (check `free -h` swap line)
- load average > number of CPU threads
- high iowait in `top` / `btop`

## Phase 4: Boot & System Health

```bash
systemd-analyze                     # total boot time
systemd-analyze blame | head -15    # slowest services
systemctl --failed                  # failed units
journalctl -p err -b --no-pager | tail -15  # errors this boot
```

### Common unnecessary latency sources
- `NetworkManager-wait-online.service` — saves 4-6s to mask
- `cloud-*.service` — cloud init on laptop? mask it
- snapd — adds ~1.7s to boot (accept unless removing snapd entirely)
- fwupd — ~1s boot cost, but worth keeping for firmware updates

## Phase 5: Applying the CPU Fix

### Immediate (runtime, resets on reboot)

```bash
# Enable turbo
echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

# Set max frequency to CPU's turbo frequency
# i7-10510U: 4900000, other CPUs: check lscpu or Intel ARK
echo 4900000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq

# Set performance governor
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Permanent (systemd service)

Create `/usr/local/bin/set-cpu-perf.sh`:
```bash
#!/bin/bash
echo 0 > /sys/devices/system/cpu/intel_pstate/no_turbo
echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
```

Create `/etc/systemd/system/cpu-perf.service`:
```ini
[Unit]
Description=Enable CPU Turbo Boost and Performance Governor
Before=multi-user.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/set-cpu-perf.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo chmod +x /usr/local/bin/set-cpu-perf.sh
sudo systemctl daemon-reload
sudo systemctl enable --now cpu-perf.service
```

## Pitfalls

- **Governor alone is not enough**: Always check `no_turbo` and `scaling_max_freq` too. The governor is the software policy; the other two are hardware/firmware limits that override it.
- **auto-cpufreq via snap is confined**: Cannot write to `intel_pstate/no_turbo` or set `scaling_max_freq`. Use the GitHub installer or the manual systemd service approach.
- **TLP + auto-cpufreq conflict**: Never install both. One sets the governor, the other resets it. Choose one.
- **Battery vs AC**: On many laptops, the CPU is hard-limited on battery no matter what software does. Diagnose with `cat /sys/class/power_supply/AC*/online` before blaming the governor.
- **SMART error log entries can be misleading**: A drive with 0 media errors but 2,898 error log entries is fine — those are recoverable NVMe command retries, not bad blocks.
- **ACPI errors are normal on Lenovo Linux**: `AE_AML_OPERAND_TYPE` errors from `_SB.HIDD._DSM` are benign and don't affect performance.
- **Uptime matters**: If the system just booted (<30 min), processes may still be settling. Check load average trend, not snapshot.

## Verification

After applying the fix:

```bash
echo "Governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
echo "Turbo: $(cat /sys/devices/system/cpu/intel_pstate/no_turbo) (0=ON)"
echo "Max freq: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)"
echo "=== Active freqs ==="
grep "MHz" /proc/cpuinfo | sort -u
echo "=== CPU-PERF Service ==="
systemctl is-enabled cpu-perf.service
systemctl is-active cpu-perf.service
```

Expected outcome:
- Governor: `performance`
- Turbo: `0` (meaning ON)
- Max freq: CPU's turbo frequency (e.g. `4900000`)
- At least some cores at 2-5 GHz under load
- Service: `enabled` + `active`

## Related

- `linux-performance-tuning` — software-level tuning (swappiness, zram, noatime, boot services)
- `thinkpad-t14-dev-setup` — T14-specific setup including local LLM inference, dev tooling
