#!/usr/bin/env python3
import subprocess
import sys
import re

test_modules = [
    ("Config & Dependencies", ["tests/test_config.py", "tests/test_dependencies.py", "tests/test_models.py"]),
    ("Technical Analysis", ["tests/test_technical_analysis.py"]),
    ("Data Collector", ["tests/test_data_collector.py"]),
    ("Fundamental Analysis", ["tests/test_fundamental_analysis.py"]),
    ("Signal Generator", ["tests/test_signal_generator.py"]),
    ("AI Interpreter", ["tests/test_ai_interpreter.py"]),
]

print("\n" + "="*70)
print("CRYPTO ANALYSIS SYSTEM - TEST CHECKPOINT SUMMARY")
print("="*70 + "\n")

total_passed = 0
total_failed = 0
total_skipped = 0
failed_tests = []

for name, modules in test_modules:
    print(f"\n{name}:")
    print("-" * 70)
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest"] + modules + ["--tb=no", "-q", "--no-header"],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    output = result.stdout + result.stderr
    
    # Parse results
    passed_match = re.search(r'(\d+) passed', output)
    failed_match = re.search(r'(\d+) failed', output)
    skipped_match = re.search(r'(\d+) skipped', output)
    
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    skipped = int(skipped_match.group(1)) if skipped_match else 0
    
    total_passed += passed
    total_failed += failed
    total_skipped += skipped
    
    status = "✅ PASS" if failed == 0 else "❌ FAIL"
    print(f"  {status} - {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed > 0:
        # Extract failed test names
        failed_lines = [line for line in output.split('\n') if 'FAILED' in line]
        for line in failed_lines[:3]:  # Show first 3
            test_name = line.split('::')[-1].split(' ')[0] if '::' in line else ''
            if test_name:
                failed_tests.append(f"  - {name}: {test_name}")

print("\n" + "="*70)
print("OVERALL SUMMARY")
print("="*70)
print(f"Total Passed:  {total_passed}")
print(f"Total Failed:  {total_failed}")
print(f"Total Skipped: {total_skipped}")
print(f"Total Tests:   {total_passed + total_failed + total_skipped}")

if failed_tests:
    print(f"\n❌ Failed Tests:")
    for test in failed_tests:
        print(test)

print("\n" + "="*70)
if total_failed == 0:
    print("✅ ALL TESTS PASSING - Ready to proceed!")
else:
    print(f"⚠️  {total_failed} tests failing - Review needed")
print("="*70 + "\n")
