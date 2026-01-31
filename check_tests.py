#!/usr/bin/env python3
import subprocess
import sys

test_modules = [
    "tests/test_config.py",
    "tests/test_dependencies.py", 
    "tests/test_models.py",
    "tests/test_technical_analysis.py",
    "tests/test_data_collector.py",
    "tests/test_fundamental_analysis.py",
    "tests/test_signal_generator.py",
    "tests/test_ai_interpreter.py",
]

results = {}
total_passed = 0
total_failed = 0
total_skipped = 0

for module in test_modules:
    print(f"\n{'='*60}")
    print(f"Testing: {module}")
    print('='*60)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", module, "--tb=no", "-q"],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    output = result.stdout + result.stderr
    print(output)
    
    # Parse results
    if "passed" in output:
        results[module] = "COMPLETED"
    elif "failed" in output:
        results[module] = "HAS FAILURES"
    else:
        results[module] = "UNKNOWN"

print(f"\n\n{'='*60}")
print("SUMMARY")
print('='*60)
for module, status in results.items():
    print(f"{module}: {status}")
