"""Backfills logical-delete status fields for existing movimentacoes.

Run after the GSI2 deployment finishes:
    python scripts/backfill_status_index.py
"""
from __future__ import annotations

import os
from typing import Any

import boto3

TABLE_NAME = os.environ["DDB_TABLE"]
TENANT_ID = "default"
ACTIVE_STATUS = "ACTIVE"


def _data_evento(item: dict[str, Any]) -> str | None:
    value = item.get("dataEvento") or item.get("dataFim")
    return str(value).strip() if value else None


def _needs_backfill(item: dict[str, Any]) -> bool:
    return not item.get("status") or not item.get("GSI2PK") or not item.get("GSI2SK")


def main() -> None:
    table = boto3.resource("dynamodb").Table(TABLE_NAME)
    last = None
    updated = 0
    skipped = 0

    while True:
        kwargs: dict[str, Any] = {
            "FilterExpression": "PK = :pk",
            "ExpressionAttributeValues": {":pk": f"TENANT#{TENANT_ID}"},
        }
        if last:
            kwargs["ExclusiveStartKey"] = last

        resp = table.scan(**kwargs)
        for item in resp.get("Items", []):
            record_id = str(item.get("id", "")).strip()
            data_evento = _data_evento(item)
            if not record_id or not data_evento or not _needs_backfill(item):
                skipped += 1
                continue

            table.update_item(
                Key={"PK": item["PK"], "SK": item["SK"]},
                UpdateExpression="SET #status = if_not_exists(#status, :active), "
                "GSI2PK = if_not_exists(GSI2PK, :gsi2pk), "
                "GSI2SK = if_not_exists(GSI2SK, :gsi2sk)",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":active": ACTIVE_STATUS,
                    ":gsi2pk": f"STATUS#{ACTIVE_STATUS}",
                    ":gsi2sk": f"{data_evento}#{record_id}",
                },
            )
            updated += 1

        last = resp.get("LastEvaluatedKey")
        if not last:
            break

    print(f"Backfill complete. updated={updated} skipped={skipped}")


if __name__ == "__main__":
    main()
