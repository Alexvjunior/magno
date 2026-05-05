import importlib.util
from pathlib import Path


def test_post_confirmation_returns_original_event():
    path = Path(__file__).resolve().parents[2] / "auth" / "triggers" / "post_confirmation.py"
    spec = importlib.util.spec_from_file_location("post_confirmation", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    event = {"userName": "user-1", "request": {"userAttributes": {"email": "a@example.com"}}}

    assert module.handler(event, None) is event
