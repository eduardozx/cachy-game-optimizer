#!/usr/bin/env python3
"""
Privileged helper for CachyOS Game Optimizer.
Run via pkexec to perform system-level optimizations requiring root.
"""

import sys
import subprocess
from pathlib import Path
import json


def write_file_content(path: str, content: str) -> dict:
    """Write content to a file (requires root)."""
    try:
        Path(path).write_text(content)
        return {"success": True, "message": f"Written to {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def append_to_file(path: str, lines: list) -> dict:
    """Append lines to a file (requires root)."""
    try:
        existing = Path(path).read_text() if Path(path).exists() else ""
        new_content = existing
        for line in lines:
            if line not in new_content:
                new_content += f"\n{line}"
        Path(path).write_text(new_content)
        return {"success": True, "message": f"Appended to {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_command(cmd: list) -> dict:
    """Run a command (requires root)."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return {"success": True, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr, "stdout": e.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}


def replace_in_file(path: str, old: str, new: str) -> dict:
    """Replace text in a file (requires root)."""
    try:
        content = Path(path).read_text()
        if old not in content:
            return {"success": False, "error": f"Pattern not found: {old}"}
        content = content.replace(old, new)
        Path(path).write_text(content)
        return {"success": True, "message": f"Replaced in {path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No action specified"}))
        sys.exit(1)

    action = sys.argv[1]
    
    actions = {
        "write_thp_enabled": lambda: write_file_content(
            "/sys/kernel/mm/transparent_hugepage/enabled", "madvise"
        ),
        "write_sysctl": lambda: append_to_file(
            "/etc/sysctl.d/99-cachy-gaming.conf",
            json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
        ),
        "write_environment": lambda: append_to_file(
            "/etc/environment",
            json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
        ),
        "update_grub_cmdline": lambda: replace_in_file(
            "/etc/default/grub",
            'GRUB_CMDLINE_LINUX_DEFAULT="',
            f'GRUB_CMDLINE_LINUX_DEFAULT="{sys.argv[2]} ' if len(sys.argv) > 2 else 'GRUB_CMDLINE_LINUX_DEFAULT="'
        ),
        "run_grub_mkconfig": lambda: run_command(["grub-mkconfig", "-o", "/boot/grub/grub.cfg"]),
        "run_sysctl_system": lambda: run_command(["sysctl", "--system"]),
        "set_power_limit": lambda: run_command(
            ["sh", "-c", f"echo {sys.argv[2]} > {sys.argv[3]}"] if len(sys.argv) > 3 else []
        ),
    }

    if action not in actions:
        print(json.dumps({"success": False, "error": f"Unknown action: {action}"}))
        sys.exit(1)

    result = actions[action]()
    print(json.dumps(result))


if __name__ == "__main__":
    main()