import json
import os

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from handlers import delete_desocupacao  # noqa: E402


def _event(record_id: str = "uuid-123", data_evento: str = "2025-07-03") -> dict:
    return {
        "pathParameters": {"id": record_id},
        "queryStringParameters": {"dataEvento": data_evento},
    }


def test_handler_marks_record_as_deleted(monkeypatch):
    calls = []

    def mark_deleted(record_id, data_evento):
        calls.append((record_id, data_evento.isoformat()))
        return True

    monkeypatch.setattr(delete_desocupacao.dynamo_repo, "mark_deleted", mark_deleted)

    response = delete_desocupacao.handler(_event(), None)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body == {"id": "uuid-123", "status": "DELETED"}
    assert calls == [("uuid-123", "2025-07-03")]


def test_handler_returns_400_for_invalid_date(monkeypatch):
    monkeypatch.setattr(delete_desocupacao.dynamo_repo, "mark_deleted", lambda *_: True)

    response = delete_desocupacao.handler(_event(data_evento="03/07/2025"), None)

    assert response["statusCode"] == 400


def test_handler_returns_404_when_record_does_not_exist(monkeypatch):
    monkeypatch.setattr(delete_desocupacao.dynamo_repo, "mark_deleted", lambda *_: False)

    response = delete_desocupacao.handler(_event(), None)

    assert response["statusCode"] == 404
