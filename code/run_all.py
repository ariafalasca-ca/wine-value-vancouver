"""Run the audit and every Part C analysis in order; stop at the first failure.
Usage (from the submission root or from code/):  python3 -I code/run_all.py
Needs data/raw/winemag-data-130k-v2.csv (see README.md). Outputs go to data/reproduced/.
Iowa: if data/raw/iowa_liquor_sales_*.csv is present the item table is rebuilt; otherwise the shipped data/iowa_750_items.csv is used.
Python 3.10+ with pandas, numpy, statsmodels, matplotlib, rapidfuzz, unidecode."""
import subprocess, sys, time, pathlib
CODE = pathlib.Path(__file__).resolve().parent
STEPS = ["audit_v5.py", "same_bottle.py", "validate_picks.py", "match_sensitivity.py", "iowa_build_items.py", "iowa_bc_benchmark.py",
         "origin_premium.py", "inflation_check.py", "make_figures.py"]
# input provenance and environment: warn (do not stop) if the raw file or library versions differ from the tested ones
import hashlib, importlib.metadata as md
sys.path.insert(0, str(CODE)); from paths import RAW_WINE
RAW_SHA256 = "52af2643c8ac29f010f0cc629dfbdda1c74aa0f332d11762af9ef3de4e567ac9"
if RAW_WINE.exists():
    h = hashlib.sha256(RAW_WINE.read_bytes()).hexdigest()
    print("raw review file sha256:", h, "(matches the tested file)" if h == RAW_SHA256 else "WARNING: differs from the tested file")
for line in (CODE / "requirements.txt").read_text().splitlines():
    if "==" in line and not line.startswith("#"):
        pkg, want = line.split("==")
        try: have = md.version(pkg)
        except md.PackageNotFoundError: have = "not installed"
        if have != want: print(f"note: {pkg} {have} installed, tested with {want}")
t0 = time.time()
for s in STEPS:
    print(f"\n=== {s} ===", flush=True); t = time.time()
    r = subprocess.run([sys.executable, "-I", str(CODE / s)], cwd=CODE)
    if r.returncode != 0:
        sys.exit(f"\nSTOPPED: {s} exited with code {r.returncode}. Outputs from earlier steps are in data/reproduced/.")
    print(f"--- {s} done in {time.time() - t:.0f}s", flush=True)
print(f"\nAll {len(STEPS)} steps finished in {time.time() - t0:.0f}s. Outputs: {(CODE.parent / 'data' / 'reproduced').as_posix()}")
