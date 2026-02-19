
IN
bash .agent/lisa/lisa.sh context health

OUT
[🔴] Context Health Report
---------------------
[📈] Saturation:      4224% (6759145 / 160000 tokens)
[📡] Signal Ratio:    Low
[rx] Status:          CRITICAL (Saturation)

LISA reports your context health is CRITICAL — the workspace token estimate is way over limit (6.7M tokens vs 160K configured limit). Signal ratio is low, meaning a lot of noise relative to signal.

Turn count is fine at 1 (green).

The saturation number is likely inflated because it's counting all files in the workspace including build/, node_modules-style artifacts, .venv/, __pycache__/, etc. You'd probably want to tune the scan exclusion patterns in the LISA config or bump context_limit to something realistic if you're using a model with a larger window.

IN
bash .agent/lisa/lisa.sh reset

OUT
[🔴] Initializing Session Reset...
[🔴] Session Archived to: .lisa/archive/20260219-104727
[🔴] State Reset to Defaults (Green/Idle).

Session reset complete. State is back to defaults (Green/Idle), scope cleared, and the previous session was archived to .lisa/archive/20260219-104727.

The checkpoint hook warned because lisa isn't on your PATH (exit 127) — it tried running lisa checkpoint as a shell command rather than through the lisa.sh wrapper. Minor config issue but non-blocking since LISA fails open.