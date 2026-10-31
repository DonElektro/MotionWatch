import os, shutil, subprocess, glob
W = "/tmp/claude-0/wt_erk2"
D = W + "/erkennungstest2"
os.makedirs(D, exist_ok=True)
if os.path.exists("/tmp/claude-0/erkt2/out/results.jsonl"):
    shutil.copy("/tmp/claude-0/erkt2/out/results.jsonl", D + "/results.jsonl")
for f in glob.glob("/tmp/claude-0/erkt2/tools/*.py") + glob.glob("/tmp/claude-0/erkt2/tools/*.sh") + ["/tmp/claude-0/erkt2/tools/results_test1.jsonl"]:
    shutil.copy(f, D + "/" + os.path.basename(f))
msg = "Erkennungstest 2: Zwischenstand Messwerte\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_019Hz7wKVUG5BNGrCZpdKc8z"
subprocess.run(["git", "-C", W, "add", "erkennungstest2"] + (["REAL_ERKENNUNG2.md"] if os.path.exists(W + "/REAL_ERKENNUNG2.md") else []))
subprocess.run(["git", "-C", W, "commit", "-q", "-m", msg])
subprocess.run(["git", "-C", W, "push", "-q", "-u", "origin", "real-erkennungstest2"])
