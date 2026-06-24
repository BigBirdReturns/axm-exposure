"""The browser demo must run the same source the tests cover: assert the
committed docs/site_data.js is exactly what tools/build_site.py produces."""

from __future__ import annotations

import importlib.util
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent

_spec = importlib.util.spec_from_file_location("build_site", REPO / "tools" / "build_site.py")
build_site = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_site)


def test_site_bundle_in_sync():
    committed = (REPO / "docs" / "site_data.js").read_text()
    assert committed == build_site.build(), "run: python tools/build_site.py"


def test_bundle_carries_package_and_examples():
    import json
    raw = build_site.build()
    payload = raw[raw.index("{"): raw.rindex("}") + 1]
    data = json.loads(payload)
    assert "axm/certify.py" in data["sources"]
    assert "lean/lean-toolchain" in data["sources"]   # report.py reads it under Pyodide
    assert "drugW_two_compartment" in data["examples"]
