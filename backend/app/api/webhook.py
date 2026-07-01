"""
app/api/webhook.py
-------------------
GitHub webhook receive endpoint.

Responsibilities:
- Accept POST /webhook/github
- Validate the X-GitHub-Event header (only 'push' is supported)
- Validate the X-Hub-Signature-256 header when a secret is configured
- Parse and validate the request body using the WebhookPayload model
- Delegate all processing to GitHubService
- Return a structured JSON response

No Git logic. No parsing logic. No filesystem logic.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.core.constants import (
    HEADER_GITHUB_EVENT,
    HEADER_GITHUB_SIGNATURE,
    SUPPORTED_GITHUB_EVENTS,
    ResponseMessage,
)
from app.dependencies import get_github_service
from app.models.webhook import WebhookPayload
from services.github_service import GitHubService
from utils.helpers import build_error_response, build_success_response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/webhook/github",
    summary="Receive GitHub Push Webhook",
    description="Accepts a GitHub push event, validates it, syncs the repository, and persists workflow state.",
    tags=["Webhook"],
)
async def receive_github_webhook(
    request: Request,
    x_github_event: str = Header(..., alias="x-github-event"),
    x_hub_signature_256: str = Header("", alias="x-hub-signature-256"),
    github_service: GitHubService = Depends(get_github_service),
) -> JSONResponse:
    """Handle an incoming GitHub push webhook.

    Args:
        request:               The raw FastAPI Request object (used to read raw body bytes).
        x_github_event:        Value of the ``X-GitHub-Event`` header.
        x_hub_signature_256:   Value of the ``X-Hub-Signature-256`` header.
        github_service:        Injected GitHubService orchestrator.

    Returns:
        JSONResponse: Success payload with workflow_id, repository, and branch,
                      or an error payload with a descriptive message.

    Raises:
        HTTPException 400: If the event type is not supported or the signature is invalid.
        HTTPException 422: If the payload fails Pydantic validation.
        HTTPException 500: If an unexpected server-side error occurs.
    """
    logger.info("Webhook received: event=%s", x_github_event)

    # ------------------------------------------------------------------ #
    # 1. Validate event type
    # ------------------------------------------------------------------ #
    if x_github_event not in SUPPORTED_GITHUB_EVENTS:
        logger.warning("Unsupported GitHub event: %s", x_github_event)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=build_error_response(ResponseMessage.UNSUPPORTED_EVENT),
        )

    # ------------------------------------------------------------------ #
    # 2. Read raw body (needed for signature verification)
    # ------------------------------------------------------------------ #
    raw_body: bytes = await request.body()

    # ------------------------------------------------------------------ #
    # 3. Validate webhook signature
    # ------------------------------------------------------------------ #
    if not github_service.verify_signature(raw_body, x_hub_signature_256):
        logger.warning("Invalid webhook signature — request rejected")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=build_error_response(ResponseMessage.INVALID_SIGNATURE),
        )

    # ------------------------------------------------------------------ #
    # 4. Parse and validate the payload
    # ------------------------------------------------------------------ #
    try:
        payload = WebhookPayload.model_validate_json(raw_body)
    except Exception as exc:
        logger.error("Payload validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=build_error_response(ResponseMessage.INVALID_PAYLOAD),
        ) from exc

    logger.info(
        "Payload validated: repo=%s  branch=%s",
        payload.repository.full_name,
        payload.branch,
    )

    # ------------------------------------------------------------------ #
    # 5. Delegate to the service layer
    # ------------------------------------------------------------------ #
    try:
        result = github_service.process_push_event(payload)
    except RuntimeError as exc:
        logger.error("Webhook processing failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=build_error_response(str(exc)),
        )

    # ------------------------------------------------------------------ #
    # 6. Return success response
    # ------------------------------------------------------------------ #
    response_body = build_success_response(
        {
            "workflow_id": result.workflow_id,
            "repository": result.repository,
            "branch": result.branch,
        }
    )
    logger.info("Response returned: workflow_id=%s", result.workflow_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content=response_body)
