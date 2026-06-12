"""
Refresh the model from your entered results.

Workflow:
  1. In the dashboard, enter final scores and click Export -> wc2026_results.json
  2. Put that file in this folder
  3. python refresh.py

It re-rates Elo from those results, regenerates match predictions and the
tournament projection (both conditioned on what actually happened), and rebuilds
index.html. Reload the dashboard to see the updated numbers for both teams.
"""
import subprocess, sys, os

steps = ["gen_predictions.py", "tournament.py", "build_dashboard.py"]

if not os.path.exists("wc2026_results.json"):
    print("note: wc2026_results.json not found - running with no entered results yet.")

for s in steps:
    print(f"\n>>> {s}")
    r = subprocess.run([sys.executable, s])
    if r.returncode != 0:
        print(f"!! {s} failed"); sys.exit(1)

print("\nDone. Reload index.html to see updated predictions and projection.")
