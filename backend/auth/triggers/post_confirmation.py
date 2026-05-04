"""Cognito Post-Confirmation trigger.

Fires after a user completes signup confirmation. Currently a no-op pass-through;
extend here to register the user in a `usuarios` DynamoDB table for auditing.
"""
from __future__ import annotations


def handler(event: dict, _context) -> dict:
    # event["userName"], event["request"]["userAttributes"]["email"], etc.
    return event
