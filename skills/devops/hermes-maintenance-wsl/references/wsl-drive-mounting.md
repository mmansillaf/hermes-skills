# Mounting Windows Drives in WSL

## Problem

A Windows drive (F:, G:, USB drive, SD card) is not visible under `/mnt/` in WSL. Only C: and D: are auto-mounted by default.

## Solution

WSL supports mounting arbitrary drives via the `drvfs` filesystem type:

```bash
# Create mount point
sudo mkdir -p /mnt/f

# Mount the drive
sudo mount -t drvfs F: /mnt/f

# Verify
ls /mnt/f/
```

## Drive Discovery

To see what drives exist in Windows:

```bash
# From WSL (uses Windows CMD)
cmd.exe /c "wmic logicaldisk get caption"
# or
cmd.exe /c "dir F:\" 2>/dev/null

# Check what's already mounted in WSL
mount | grep drvfs
ls /mnt/
```

## Unmounting

```bash
sudo umount /mnt/f
```

## Permissions

Drives mounted via `drvfs` show files as owned by `root:root` with `rwxrwxrwx` permissions. You can read files without sudo in most cases.

## Common Issues

| Issue | Fix |
|---|---|
| `mount: /mnt/f: mount point does not exist` | Run `sudo mkdir -p /mnt/f` first |
| `mount error(5): Input/output error` | Drive may be in use by Windows (close file explorer windows) |
| `Transport endpoint not connected` | Remount: `sudo umount /mnt/f && sudo mount -t drvfs F: /mnt/f` |
| Path case mismatch | WSL is case-sensitive, Windows is not. Use lowercase for `drvfs` but uppercase for the drive letter |
