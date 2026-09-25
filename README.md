# Long Task Runner for Codex

Run long, non-interactive commands offline so Codex can stop polling. The skill records a log and exit code, gives a predicted completion time, and resumes the original task when you return to the conversation. It does not notify or wake Codex automatically.

## Requirements

| System | Requirements | Command shell used by the runner |
| --- | --- | --- |
| Linux | Python 3.10+, Git, tmux | `/bin/sh` |
| macOS | Python 3.10+, Git, tmux | `/bin/sh` |
| Windows | Python 3.10+, Git, PowerShell | PowerShell |

On Ubuntu/Debian, install dependencies with `sudo apt-get install python3 git tmux`. On Fedora, use `sudo dnf install python3 git tmux`. On macOS with Homebrew, use `brew install python git tmux`. On Windows, install [Python](https://www.python.org/downloads/windows/) and [Git](https://git-scm.com/download/win); PowerShell is already included with Windows. Windows uses its native detached-process backend and does not need tmux.

## Install globally

Clone the repository into Codex's user skill directory. If `CODEX_HOME` is set, use its `skills` directory instead of the default path.

Linux/macOS:

```bash
skill_root="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$skill_root"
git clone https://github.com/KATe-AGI/long-task-runner.git "$skill_root/long-task-runner"
```

Windows PowerShell:

```powershell
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex\skills' }
New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
git clone https://github.com/KATe-AGI/long-task-runner.git (Join-Path $skillRoot 'long-task-runner')
```

**Default: explicit invocation.** The included `agents/openai.yaml` sets `allow_implicit_invocation: false`. Invoke `$long-task-runner` when you want Codex to use it.

**Recommended: global automatic invocation.** After installing globally, change `allow_implicit_invocation` to `true` in `<Codex skills>/long-task-runner/agents/openai.yaml`. Codex can then select the skill for commands likely to run longer than two minutes. It asks `实际任务是否属于长任务？` with **是/不是** answers only when it cannot quickly judge the task type. Restart or open a new Codex conversation after changing skill settings.

## Direct runner usage

On Linux/macOS, replace `python` with `python3`:

```text
python scripts/long_task.py start --name build --estimate '30 minutes' --cwd <project-directory> --cmd '<command>'
python scripts/long_task.py status --run-dir <run-directory>
python scripts/long_task.py log --run-dir <run-directory> --tail 40
```

The run directory is `<project-directory>/.codex-runs/<run-id>/`. It contains `metadata.json`, `output.log`, and, after completion, `exit_code`. The command is executed using the system shell listed above. Keep credentials out of command arguments because they may appear in process listings.
