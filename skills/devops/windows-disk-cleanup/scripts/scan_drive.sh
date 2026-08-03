#!/usr/bin/env bash
# scan_drive.sh — Top-level directory size scan of a Windows NTFS drive, PowerShell-native.
# Usage: scan_drive.sh [DRIVE_LETTER]   (default: D)
# Why: `du` over /mnt (9p) is pathologically slow on NTFS; powershell.exe is seconds-fast.
# Requires: powershell.exe reachable from WSL (always true on Windows 10/11).

DRIVE="${1:-D}"

powershell.exe -NoProfile -Command "Get-ChildItem -Path '${DRIVE}:\' -Directory -Force -ErrorAction SilentlyContinue | ForEach-Object { try { \$size = (Get-ChildItem -Path \$_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum; [PSCustomObject]@{Dir=\$_.Name; GB=[math]::Round(\$size/1GB,2)} } catch { [PSCustomObject]@{Dir=\$_.Name; GB='ERR'} } } | Sort-Object GB -Descending | Format-Table -AutoSize" 2>/dev/null

echo "---"
df -h "/mnt/${DRIVE,,}" | tail -1
