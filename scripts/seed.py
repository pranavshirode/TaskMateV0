"""Seed demo data. Wrapper kept so `python scripts/seed.py` works from the repo root.

The implementation lives in apps/api/scripts/seed_db.py so it is also available inside the API container.
"""

import os
import runpy

runpy.run_path(
    os.path.join(os.path.dirname(__file__), "..", "apps", "api", "scripts", "seed_db.py"),
    run_name="__main__",
)
