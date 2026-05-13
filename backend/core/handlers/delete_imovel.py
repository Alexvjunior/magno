"""DELETE /imoveis/{idImovel} -- marks an imovel as deleted."""
from __future__ import annotations

from infra import dynamo_repo

from ._common import json_response


def handler(event: dict, _context) -> dict:
    id_imovel = (event.get("pathParameters") or {}).get("idImovel", "").strip()
    if not id_imovel:
        return json_response(400, {"errors": {"idImovel": "idImovel obrigatorio"}})

    deleted = dynamo_repo.mark_imovel_deleted(id_imovel)
    if not deleted:
        return json_response(404, {"message": "Imovel nao encontrado"})

    return json_response(200, {"idImovel": id_imovel, "status": "DELETED"})
