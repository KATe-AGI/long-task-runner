---
name: long-task-runner
description: For shell commands likely to exceed two minutes, start them offline on Linux, Windows, or macOS and stop Codex polling; ask the user only when the task type is unclear.
---

# Long Task Runner

Use this skill when an upcoming shell command could run longer than about two minutes. Its purpose is to avoid repeated Codex polling and the resulting token cost. Linux and macOS use `tmux`; Windows uses a native detached process. Run the helper with `python3` on Linux/macOS or `python` on Windows.

## Decide the task type

Quickly judge whether the command is a long task. If it clearly is, use this skill. If it clearly is not, use Codex's native workflow without applying this skill. Only when the type cannot be judged quickly, write a short description of the actual task followed by `是否属于长任务？`, then wait for the user's answer. The question box must show the real task description, never the placeholder text `<任务>`. Use these fixed answers:

```text
是
不是
```

For example, ask `运行项目测试是否属于长任务？` when that is the actual task. If the user answers `不是`, use Codex's native workflow without applying this skill. If the user answers `是`, use this skill. Estimate the duration from the available task context and label uncertain estimates as such.

## Launch and stop

For a long task, choose a short run name using lowercase letters, digits, `_`, or `-`, then run:

```text
<python> '<skill-dir>/scripts/long_task.py' start --name <run-name> --estimate '<estimated-duration>' --cwd '<working-directory>' --cmd '<shell-command>'
```

The command runs under `/bin/sh` on Linux/macOS and PowerShell on Windows. The helper prints the run directory, session or process ID, log path, and start time. Check status once:

```text
<python> '<skill-dir>/scripts/long_task.py' status --run-dir '<run-dir>'
```

If the task has already finished, read its result and continue the original work. Otherwise, give the user the run ID, log path, observed status, and a **predicted completion time** calculated from the start time and estimated duration. Show a time range when the estimate is uncertain. Tell the user to return around that time with this fixed message, then end the turn without further polling:

```text
继续长任务 <run-id>；请检查 <run-dir> 的退出码和日志，并继续原任务。
```

On that later turn, check `status` once and read the relevant log tail with `log --run-dir '<run-dir>' --tail 40`. If the task is still running, report that once and stop. This skill does not wake Codex automatically.
