#!/usr/bin/env python3
"""Run a finite shell command in a detached tmux session."""

from __future__ import annotations

import argparse
from collections import deque
import datetime as dt
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import subprocess
import sys


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def write_json(path: Path, data: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def tmux_alive(session: str) -> bool:
    return subprocess.run(
        ["tmux", "has-session", "-t", f"={session}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def start(args: argparse.Namespace) -> int:
    if os.name == "nt" or not shutil.which("tmux"):
        raise RuntimeError("tmux is required; run this script inside Linux, macOS, or WSL")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", args.name):
        raise ValueError("--name must use lowercase letters, digits, underscores, or hyphens")
    cwd = Path(args.cwd).expanduser().resolve(strict=True)
    if not cwd.is_dir():
        raise ValueError("--cwd must be a directory")
    if not args.cmd.strip():
        raise ValueError("--cmd must not be empty")

    run_id = f"{args.name}-{dt.datetime.now(dt.timezone.utc):%Y%m%dT%H%M%SZ}-{secrets.token_hex(3)}"
    run_dir = cwd / ".codex-runs" / run_id
    run_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    session = f"codex_{run_id}"
    metadata = {
        "run_id": run_id,
        "session": session,
        "cwd": str(cwd),
        "estimate": args.estimate,
        "started_at": utc_now(),
        "log_path": str(run_dir / "output.log"),
    }
    write_json(run_dir / "metadata.json", metadata)
    command_path = run_dir / "command.tmp"
    descriptor = os.open(command_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(args.cmd)

    pane_command = " ".join(
        shlex.quote(part)
        for part in (sys.executable, str(Path(__file__).resolve()), "_run", "--run-dir", str(run_dir))
    )
    result = subprocess.run(
        ["tmux", "new-session", "-d", "-s", session, pane_command],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        command_path.unlink(missing_ok=True)
        raise RuntimeError(f"tmux failed to start: {result.stderr.strip()}")
    print(json.dumps({**metadata, "run_dir": str(run_dir)}, indent=2))
    return 0


def run_inside(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).resolve(strict=True)
    metadata = read_json(run_dir / "metadata.json")
    command_path = run_dir / "command.tmp"
    command = command_path.read_text(encoding="utf-8")
    command_path.unlink()
    write_json(run_dir / "state.json", {"status": "running", "started_at": utc_now()})
    try:
        with (run_dir / "output.log").open("ab", buffering=0) as output:
            result = subprocess.run(
                command,
                shell=True,
                executable="/bin/sh",
                cwd=metadata["cwd"],
                stdout=output,
                stderr=subprocess.STDOUT,
                check=False,
            )
        exit_code = result.returncode
    except Exception as error:
        with (run_dir / "output.log").open("a", encoding="utf-8") as output:
            output.write(f"\nRunner error: {error}\n")
        exit_code = 125
    (run_dir / "exit_code").write_text(f"{exit_code}\n", encoding="utf-8")
    write_json(
        run_dir / "state.json",
        {"status": "succeeded" if exit_code == 0 else "failed", "exit_code": exit_code, "ended_at": utc_now()},
    )
    return 0


def status(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve(strict=True)
    metadata = read_json(run_dir / "metadata.json")
    state_path = run_dir / "state.json"
    if state_path.exists():
        state = read_json(state_path)
    else:
        state = {"status": "starting"}
    if state["status"] in {"starting", "running"}:
        if not shutil.which("tmux"):
            state = {"status": "unknown", "reason": "tmux is unavailable"}
        elif not tmux_alive(metadata["session"]):
            exit_path = run_dir / "exit_code"
            if exit_path.exists():
                code = int(exit_path.read_text(encoding="utf-8").strip())
                state = {"status": "succeeded" if code == 0 else "failed", "exit_code": code}
            else:
                state = {"status": "interrupted", "reason": "tmux session ended without an exit code"}
    print(json.dumps({**metadata, "run_dir": str(run_dir), **state}, indent=2))
    return 0


def log(args: argparse.Namespace) -> int:
    log_path = Path(args.run_dir).expanduser().resolve(strict=True) / "output.log"
    if not log_path.exists():
        print("No log yet.")
        return 0
    with log_path.open("r", encoding="utf-8", errors="replace") as stream:
        sys.stdout.writelines(deque(stream, maxlen=args.tail))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    start_parser = subparsers.add_parser("start", help="launch a detached tmux job")
    start_parser.add_argument("--name", required=True)
    start_parser.add_argument("--estimate", default="unknown")
    start_parser.add_argument("--cwd", required=True)
    start_parser.add_argument("--cmd", required=True)
    start_parser.set_defaults(func=start)
    for action, function in (("status", status), ("log", log), ("_run", run_inside)):
        action_parser = subparsers.add_parser(action, help=argparse.SUPPRESS if action == "_run" else None)
        action_parser.add_argument("--run-dir", required=True)
        if action == "log":
            action_parser.add_argument("--tail", type=int, default=40)
        action_parser.set_defaults(func=function)
    args = parser.parse_args()
    if args.action == "log" and args.tail < 1:
        parser.error("--tail must be positive")
    try:
        return args.func(args)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
