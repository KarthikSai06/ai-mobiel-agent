"""Small diagnostic — run outcome/loop tests with verbose traceback captured."""
import subprocess, sys, io

result = subprocess.run(
    [sys.executable, "-m", "pytest",
     "tests/test_agent_fixes.py::TestOutcomeTracking",
     "tests/test_agent_fixes.py::TestLoopDetector",
     "--tb=long", "-s"],
    cwd=r"d:\projects\mobile_agent",
    capture_output=True, text=True
)
print(result.stdout[-5000:])
print(result.stderr[-2000:])
