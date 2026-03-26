import os
from contextlib import suppress

if os.getenv("COVERAGE_PROCESS_START"):
    with suppress(Exception):
        import coverage

        coverage.process_startup()
