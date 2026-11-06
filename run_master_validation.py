import subprocess
import sys

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

suites = [
    ("Step 3: Database & Validation", "test_step3.py"),
    ("Step 4: Lead Scoring Formula", "test_lead_scoring.py"),
    ("Step 5: Follow-Up Automation", "test_followups.py"),
    ("Step 9: Complete End-to-End CRM", "test_end_to_end.py"),
    ("Step 11: Gemini AI Service & Fallback", "test_ai_service.py"),
    ("Step 12: Advanced AI & Interior Design", "test_advanced_ai.py"),
    ("Step 14: Hyderabad Edition Transformation", "test_hyderabad_migration.py"),
    ("Step 15: Hyderabad Dashboard Redesign", "test_hyderabad_dashboard.py"),
    ("Step 16: Hyderabad Locality Filters & Display", "test_hyderabad_locality_filters.py")
]

results = []
print("\n" + "=" * 65)
print("EXECUTING ALL 8 SUITES ACROSS THE SHA INTERIORS CODEBASE")
print("=" * 65)

for title, script in suites:
    res = subprocess.run([sys.executable, script], capture_output=True, text=True)
    passed = (res.returncode == 0)
    status_str = "PASSED [100%]" if passed else "FAILED"
    results.append((title, status_str, passed, res.stderr or res.stdout[-300:] if not passed else ""))
    print(f"{title:<45} : {status_str}")

print("=" * 65)
all_ok = all(r[2] for r in results)
print(f"ALL 8 TEST SUITES PASSED: {all_ok}")
print("=" * 65)

if not all_ok:
    print("\nFailure Details:")
    for title, status, passed, err in results:
        if not passed:
            print(f"\n--- {title} ---")
            print(err)
    sys.exit(1)
