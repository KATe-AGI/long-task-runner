# Long Task Runner for Codex

A Codex skill for launching long, non-interactive shell commands in detached tmux sessions. It records logs and exit codes so you can return to the task later without keeping the Codex tool call open.

## Requirements

Run inside Linux, macOS, or WSL with Python 3.10+ and `tmux` installed. Native Windows PowerShell is not supported.

## Install

Copy this repository to your Codex skills directory as `long-task-runner`, then invoke `$long-task-runner` or let Codex select it for a suitable long-running command.

## Example

```bash
python3 scripts/long_task.py start \
  --name build --estimate unknown \
  --cwd /path/to/project --cmd 'make all'

python3 scripts/long_task.py status --run-dir /path/to/project/.codex-runs/<run-id>
python3 scripts/long_task.py log --run-dir /path/to/project/.codex-runs/<run-id> --tail 40
```

The helper starts a tmux session, writes `metadata.json`, `state.json`, `output.log`, and `exit_code` in the run directory, and prints the paths needed to inspect the run. Jobs do not notify or wake Codex automatically. Return to the original Codex conversation and ask it to continue after the job finishes.

Run the integration check on a Linux, macOS, or WSL machine with tmux available:

```bash
python3 -m unittest discover -s tests -v
```

Shell commands are executed by `/bin/sh`. Keep secrets out of command arguments because they may appear in process listings. The run directory should be kept private if command output or logs are sensitive.
