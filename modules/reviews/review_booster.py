from typing import Dict, Any
import logging
from datetime import datetime

from modules.ai.base import BaseAIHandler

logger = logging.getLogger(__name__)


def request_positive_review(order_id: str, order_context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a personalized review request if transaction was smooth."""
    handler = BaseAIHandler(response_mime_type='application/json')
    prompt = {
        'task': 'Generate a short, friendly, non-pushy review request tailored to the customer and transaction tone.',
        'order_id': order_id,
        'order': order_context,
        'instructions': 'Return JSON: { message: string, send: bool }'
    }
    resp = handler.generate(str(prompt))
    if not resp.get('ok'):
        logger.warning('Review booster AI failed: %s', resp.get('error'))
        # fallback generic message
        msg = f"Dziękujemy za zakup! Jeśli jesteś zadowolony z {order_context.get('items',[{}])[0].get('product_name','produktu')}, zostaw proszę krótką opinię."
        return {'ok': True, 'message': msg, 'send': True}

    parsed = resp.get('response') or {}
    return {'ok': True, 'message': parsed.get('message', ''), 'send': bool(parsed.get('send', True)), 'ts': datetime.utcnow().isoformat()}
