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

### Recommended: ask Codex to install and enable automatic invocation

Paste this message into Codex on the machine where you want the skill installed. It also works when an older copy is already installed:

```text
请在这台机器上全局安装或更新 https://github.com/KATe-AGI/long-task-runner，并启用 Codex 自动调用。先确定当前 Codex 实际使用的 CODEX_HOME；若未设置，使用当前用户的 ~/.codex（Windows 为 %USERPROFILE%\.codex）。把仓库放在该目录的 skills/long-task-runner 下；若已安装，先核对仓库来源并保留现有本地改动，再安全更新。按 README 安装当前系统缺少的运行依赖。将该技能 agents/openai.yaml 中的 policy.allow_implicit_invocation 设为 true，保留其他配置。最后核验 SKILL.md、运行脚本、依赖和该配置都位于实际技能目录，报告安装路径及检查结果，并提醒我开启新的 Codex 会话。不要只克隆仓库就宣称已启用自动调用。
```

The repository defaults to explicit invocation (`allow_implicit_invocation: false`), so copying or cloning it alone will **not** enable automatic selection. Setting the policy to `true` allows Codex to select the skill; actual selection still depends on the command and the skill description.

### Manual installation (explicit invocation by default)

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
