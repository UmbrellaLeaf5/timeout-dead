# AI Agent Recovery Example

This example shows a case where `timeout-dead` kept an AI agent from getting stuck on a bad assumption and gave it a chance to recover on its own.

> This session was recorded with `timeout-dead` 0.4.4. The agent commentary, commands, and
> command-output blocks below are preserved as captured.

## Scenario

The agent needs to start a Spring Boot backend and wait until the service is ready. Its approach is straightforward:

1. Start the backend in the background with `nohup` and `&`.
2. Poll the log for the startup message.
3. Continue once the expected pattern appears.

The problem is that the agent guesses the wrong application name. That makes the polling condition impossible to satisfy, so the loop would run indefinitely without an external timeout.

---

## Step 1: Start the Backend

**Agent's reasoning:**

> Port 8081 is free. Now let me start Root Backend.

**Command executed:**

```bash
time-d -c "nohup ./gradlew bootRun --args='--spring.profiles.active=dev' > /tmp/root-backend.log 2>&1 & echo PID=\$!"
```

**Output:**

```
Running: nohup ./gradlew bootRun --args='--spring.profiles.active=dev' > /tmp/root-backend.log 2>&1 & echo PID=$!

Timeout: 60.0 seconds


Err:


Out:


PID=979


Exit code: 0

```

The launch command succeeds and returns PID `979`, so the agent moves on to waiting for the service to report that it is ready.

---

## Step 2: Wait for the Backend to Become Ready

**Agent's reasoning:**

> Root backend is starting. Let me wait for it to be ready. I'll wait 50 seconds then check the log.

**Command executed:**

```bash
time-d -c --sec 70 "while ! grep -q 'Started RootApplicationKt' /tmp/root-backend.log 2>/dev/null; do sleep 3; done && echo READY"
```

**Output:**

```
Running: while ! grep -q 'Started RootApplicationKt' /tmp/root-backend.log 2>/dev/null; do sleep 3; done && echo READY

Timeout: 70.0 seconds


Timeout exceeded 70.0 seconds

Err:


Out:


Exit code: 3221225786

```

The timeout is the first sign that the readiness check is wrong. The agent is waiting for `Started RootApplicationKt`, but that string never appears in the log. Because the loop has no exit path until `grep` matches, it would otherwise keep running.

Here, `timeout-dead` stops the command after 70 seconds and returns a non-zero exit code. Instead of leaving the agent blocked in the polling loop, it turns the bad readiness check into a failure the agent can inspect.

On Windows, exit code `3221225786` indicates that the process was terminated by a signal (`STATUS_CONTROL_C_EXIT` or similar), which is consistent with a timed-out process being force-stopped.

---

## Step 3: Investigate the Failure

**Agent's reasoning:**

> The root backend didn't start within 70 seconds. Let me check the log to see what's happening now.

**Command executed:**

```bash
time-d -c "tail -30 /tmp/root-backend.log"
```

**Output (truncated):**

```
Running: tail -30 /tmp/root-backend.log

Timeout: 60.0 seconds


Err:


Out:


2026-08-01T00:07:26.541+03:00  INFO 17144 --- [factory-root] [           main] s.g.d.d.f.r.s.c.ExceptionModeInitializer : Initialized Application Exception Handling with mode: dev
2026-08-01T00:07:29.230+03:00  INFO 17144 --- [factory-root] [           main] o.s.boot.tomcat.TomcatWebServer          : Tomcat started on port 8081 (http) with context path '/'
2026-08-01T00:07:29.250+03:00  INFO 17144 --- [factory-root] [           main] s.g.d.d.f.root.FactoryApplicationKt      : Started FactoryApplicationKt in 16.775 seconds (process running for 17.481)
2026-08-01T00:07:29.339+03:00  WARN 17144 --- [factory-root] [           main] o.s.core.events.SpringDocAppInitializer  : SpringDoc /api-docs endpoint is enabled by default...
...


Exit code: 0

```

**Agent's realization:**

> Root Backend IS running! The Started FactoryApplicationKt line is there. It started on port 8081.

The log makes the issue clear: the service started successfully in about 16.8 seconds, but its startup message contains `FactoryApplicationKt`, not `RootApplicationKt`. The service was healthy; only the readiness check was wrong.

---

## What Happened

Without the timeout wrapper, the polling command would have looked like this:

```bash
while ! grep -q 'Started RootApplicationKt' /tmp/root-backend.log 2>/dev/null; do sleep 3; done && echo READY
```

Since `Started RootApplicationKt` never appears, `grep` never succeeds and the loop never ends. There is nothing inside the command that would cause it to recover from the bad assumption.

With `timeout-dead` in place, the sequence is different:

| Step | What happened                                                        |
| ---- | -------------------------------------------------------------------- |
| 1    | `timeout-dead` enforced a 70-second limit on the polling loop.       |
| 2    | The process was killed, and the agent received a non-zero exit code. |
| 3    | The agent recognized the failure and investigated the log.           |
| 4    | The agent discovered the actual startup message.                     |
| 5    | The agent adjusted its approach and continued working.               |

The important part is not that the timeout fixes the bad condition. It does not. It gives the caller a bounded failure instead of an unbounded wait, which makes recovery possible.

## Technical Details

### Exit Code

| Exit Code    | Meaning                                                                                             |
| ------------ | --------------------------------------------------------------------------------------------------- |
| `0`          | Success (command completed normally)                                                                |
| `3221225786` | Windows-specific code indicating process was killed by signal (e.g., `SIGKILL` from `timeout-dead`) |

### Polling Command

```bash
time-d -c --sec 70 "while ! grep -q 'Started RootApplicationKt' /tmp/root-backend.log 2>/dev/null; do sleep 3; done && echo READY"
```

| Component          | Purpose                                    |
| ------------------ | ------------------------------------------ |
| `time-d -c`        | Run `timeout-dead` in capture-output mode  |
| `--sec 70`         | Set timeout to 70 seconds                  |
| `while ! grep ...` | Loop until the pattern appears in the log  |
| `sleep 3`          | Poll every 3 seconds to avoid CPU spinning |
| `&& echo READY`    | Print "READY" when the condition is met    |

The mismatch was simply the application class name:

| Searched For                | Actual Pattern                 |
| --------------------------- | ------------------------------ |
| `Started RootApplicationKt` | `Started FactoryApplicationKt` |

The agent assumed the backend's main class was `RootApplicationKt`; the running application reported `FactoryApplicationKt` instead.

## Takeaway

This is a useful example of why long-running or polling commands need a hard upper bound. A timeout cannot prevent the agent from making a wrong assumption, but it can prevent that mistake from turning into a permanent stall.

Once the polling loop timed out, the agent had enough information to inspect the log, identify the mismatch, and continue without human intervention.

## Recommended Practices for AI Agents

1. Put a timeout around polling loops so a bad condition cannot block indefinitely:

   ```bash
   time-d --sec <reasonable_limit> "while ! check_condition; do sleep N; done"
   ```

2. Use `-c` when captured output is easier for the caller to inspect:

   ```bash
   time-d -c "command_with_output"
   ```

3. After a timeout, inspect the relevant logs before retrying:

   ```bash
   time-d -c "tail -50 /path/to/log"
   ```

4. Choose the timeout based on how long the operation normally takes:
   - Gradle builds: 300-600 seconds
   - Service startup: 30-90 seconds
   - Quick checks: 5-10 seconds

5. Treat non-zero exit codes as a signal to inspect what failed rather than blindly repeating the same command.

## See Also

- [`README.md`](./README.md) — installation, usage, and reference documentation
- [`AGENTS.md`](./AGENTS.md) — agent workflow rules
- [`CODE-STYLE.md`](./CODE-STYLE.md) — coding standards

---

_This example comes from a real AI agent session in which a timeout converted a bad readiness check into a recoverable failure._
