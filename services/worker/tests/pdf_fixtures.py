"""Re-export the API test suite's PDF builder so both suites share one implementation."""

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[2] / "api" / "tests" / "pdf_fixtures.py"
_spec = importlib.util.spec_from_file_location("api_pdf_fixtures", _path)
assert _spec is not None and _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

make_pdf = _module.make_pdf
