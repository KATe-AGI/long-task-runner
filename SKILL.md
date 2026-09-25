---
name: long-task-runner
description: Launch likely multi-minute, non-interactive shell jobs in detached tmux sessions on Linux, macOS, or WSL; record logs and exit status for a later user-requested follow-up.
---

# Long Task Runner

Use this skill when a shell command is likely to run longer than about two minutes, or its duration is uncertain and it could reasonably exceed two minutes. Examples include training, evaluation, large preprocessing, builds, downloads, and benchmarks. Short commands and commands needing an interactive prompt or live terminal stay in the normal workflow.

Run the helper **inside** Linux, macOS, or WSL, with `python3` and `tmux` installed. The helper is [scripts/long_task.py](scripts/long_task.py). It launches one finite command in a detached tmux session and writes its log and exit code under `<cwd>/.codex-runs/<run-id>/`. It does not notify or wake Codex when the job finishes.

## Launch

1. Decide the command and working directory. Use a short run name containing lowercase letters, digits, `_`, or `-`. Estimate duration only from evidence; otherwise use `unknown`.
2. Launch:

   ```bash
   python3 <skill-dir>/scripts/long_task.py start \
     --name <run-name> --estimate '<estimate-or-unknown>' \
     --cwd '<working-directory>' --cmd '<shell-command>'
   ```

   The helper prints the run ID, tmux session, run directory, log path, and start time. Quote the shell command for the invoking shell. Avoid passing credentials in command arguments; arguments can appear in process listings.
3. Make at most one short startup check with `status` and, if useful, `log --tail 40`. If the session is running and no launch error is visible, stop checking. Do not attach to the pane or poll for completion in this turn.
4. Report the run ID, session, working directory, concise command, log and run directory paths, start time, estimate, startup status, and how the user can inspect the job (`tmux attach -t <session>` or the commands below). Redact secrets from the report. End with the exact message the user can send to resume the original work:

   ```text
   继续处理长任务 <run-id>。请检查 <run-dir> 的状态、exit_code 和日志；成功后继续原任务，失败时定位原因。不要持续轮询。
   ```

   Include any already requested post-run action in that message.

## Inspect later

```bash
python3 <skill-dir>/scripts/long_task.py status --run-dir '<run-dir>'
python3 <skill-dir>/scripts/long_task.py log --run-dir '<run-dir>' --tail 40
```

On a later user turn, check status once and read only the relevant log tail or result files. Continue the original workflow if the job finished. If it is still running, report that once and stop. If a subsequent step is also long, launch it as a separate run.

The helper does not change the permission needed for the underlying command. Do not detach interactive commands, privileged or destructive operations merely because they are slow. Do not invent an ETA or claim automatic notification.
