import logging
import os

import africastalking

logger = logging.getLogger(__name__)

_sms_client = None


def _get_client():
    global _sms_client
    if _sms_client is not None:
        return _sms_client

    username = os.getenv("AT_USERNAME")
    api_key = os.getenv("AT_API_KEY")
    if not username or not api_key:
        raise ValueError("Missing AT_USERNAME or AT_API_KEY environment variables")

    africastalking.initialize(username, api_key)
    _sms_client = africastalking.SMS
    return _sms_client


def send_sms(to: str, message: str) -> None:
    """Send an SMS via Africa's Talking. Logs and swallows errors so a delivery
    failure never breaks the processing flow that triggered it."""
    try:
        client = _get_client()
        sender_id = os.getenv("AT_SENDER_ID")
        if sender_id:
            response = client.send(message, [to], sender_id)
        else:
            response = client.send(message, [to])
        logger.info(f"SMS sent to {to}: {response}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {to}: {e}")
