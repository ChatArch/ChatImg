from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def isolate_chatarch_home(monkeypatch, tmp_path):
    """Keep tests away from the operator's real ChatEnv profiles and tokens."""

    monkeypatch.setenv("CHATARCH_HOME", str(tmp_path / "chatarch-home"))
