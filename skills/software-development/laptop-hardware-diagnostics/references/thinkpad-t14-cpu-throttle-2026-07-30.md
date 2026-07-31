# CPU Throttle Diagnosis — Real-time Session (2026-07-30)

## Machine
Lenovo ThinkPad T14 Gen 1 (i7-10510U, 4C/8T, 32GB DDR4)
OS: Ubuntu 24.04, kernel 7.0.0-28-generic
Disk: Toshiba KBG30ZMV256G (NVMe)

## Initial Complaint
User felt the system was slow/unresponsive.

## Diagnostics Performed

### Step 1 — Baseline
```bash
hostname && uname -a && uptime
free -h
df -h /
lscpu | grep "Model name"
grep "MHz" /proc/cpuinfo
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

### Step 2 — Governor identified as `powersave`
```
scaling_governor = powersave
CPU MHz: 400-800 MHz across all 8 cores
```

### Step 3 — Deeper check revealed TWO more limiters
```bash
cat /sys/devices/system/cpu/intel_pstate/no_turbo        # → 1 (turbo OFF)
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq  # → 800000 (capped)
```

**Three independent limiters were active simultaneously:**
1. Governor = `powersave` (software)
2. `no_turbo = 1` (firmware flag)
3. `scaling_max_freq = 800000` (hardware cap)

### Step 4 — Disk health (SMART PASSED)
- Model: Toshiba KBG30ZMV256G
- Temperature: 38°C
- Available Spare: 100%
- Percentage Used: 14%
- Data Written: 17.3 TB
- Power On Hours: 20,580 (~2.35 years)
- Power Cycles: 1,275
- Unsafe Shutdowns: 102 (~8% of cycles)
- Media Errors: 0
- Error Log Entries: 2,898 (recoverable retries, not bad blocks)

### Step 5 — System errors (benign)
Only ACPI errors from `_SB.HIDD._DSM` (typical Lenovo + Linux) and
gnome-keyring init failures. No hardware or driver errors.

## The Fix Applied

### Runtime
```bash
echo 0 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo
echo 4900000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Permanent (systemd service: cpu-perf.service)
Created `/usr/local/bin/set-cpu-perf.sh` + systemd oneshot service.
Enabled and active.

## Results After Fix
```
Governor: performance
Turbo: 0 (ON)
Max freq: 4900000 (4.9 GHz)
Active freqs: 4 cores at 4.4-4.9 GHz, 4 cores idling at 400 MHz
```

## Notes for Future
- auto-cpufreq snap version CANNOT fix `no_turbo` or `scaling_max_freq` — confinement.
- TLP and auto-cpufreq conflict — choose one.
- Turbo may re-disable on battery (firmware decision, not software-controllable).
- SMART error log entries ≠ bad blocks when media errors = 0.
