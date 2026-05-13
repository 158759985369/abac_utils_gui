# ABAC GUI

This project is a clean rebuild of `abac_gui` based on `abac_gui开发设计文档.md`.

Frozen first-version constraints:

1. Target platform is Linux only.
2. The GUI must be started as root.
3. The GUI must not write `/etc/abac/*.json` directly.
4. All write operations must go through the real `abac` CLI or `systemctl`.
5. Interactive write operations are driven through `pexpect`.

Recommended launch command on the target Linux machine:

```bash
sudo --preserve-env=DISPLAY,XAUTHORITY python3 main.py
```

Runtime dependencies:

- Python 3
- PyQt5
- pexpect

