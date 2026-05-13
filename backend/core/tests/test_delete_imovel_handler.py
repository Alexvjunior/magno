import json
import os

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_EC2_METADATA_DISABLED", "true")

from handlers import delete_imovel  # noqa: E402


def test_handler_marks_imovel_as_deleted(monkeypatch):
    calls = []
    monkeypatch.setattr(delete_imovel.dynamo_repo, "mark_imovel_deleted", lambda id_imovel: calls.append(id_imovel) or True)

    response = delete_imovel.handler(
        {"pathParameters": {"idImovel": "FLORIANOPOLIS|PLAZA MEDITERRANEO|326"}},
        None,
    )
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body == {
        "idImovel": "FLORIANOPOLIS|PLAZA MEDITERRANEO|326",
        "status": "DELETED",
    }
    assert calls == ["FLORIANOPOLIS|PLAZA MEDITERRANEO|326"]


def test_handler_requires_id_imovel(monkeypatch):
    calls = []
    monkeypatch.setattr(delete_imovel.dynamo_repo, "mark_imovel_deleted", lambda id_imovel: calls.append(id_imovel) or True)

    response = delete_imovel.handler({"pathParameters": {"idImovel": " "}}, None)

    assert response["statusCode"] == 400
    assert calls == []


def test_handler_returns_404_when_imovel_is_missing(monkeypatch):
    monkeypatch.setattr(delete_imovel.dynamo_repo, "mark_imovel_deleted", lambda *_: False)

    response = delete_imovel.handler({"pathParameters": {"idImovel": "missing"}}, None)

    assert response["statusCode"] == 404
    assert json.loads(response["body"])["message"] == "Imovel nao encontrado"
