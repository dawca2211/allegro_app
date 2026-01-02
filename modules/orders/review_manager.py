from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Simple in-memory queue for scheduled review messages
_REVIEW_QUEUE: List[Dict[str, Any]] = []
_SENT: List[Dict[str, Any]] = []


def enqueue_review_on_delivery(order_data: Dict[str, Any]):
    """Schedule a review request 3 days after delivery. order_data must include order_id and customer info."""
    order_id = order_data.get('order_id') or order_data.get('id')
    if not order_id:
        logger.warning('enqueue_review: missing order id')
        return {'ok': False, 'error': 'missing_order_id'}

    # due in 3 days
    due = datetime.utcnow() + timedelta(days=3)
    _REVIEW_QUEUE.append({'order_id': order_id, 'due': due, 'order': order_data})
    logger.info('Enqueued review for %s at %s', order_id, due.isoformat())
    return {'ok': True, 'order_id': order_id, 'due': due.isoformat()}


def run_due_reviews(now: datetime = None) -> Dict[str, Any]:
    """Process queued reviews that are due. Returns summary of sent messages."""
    from modules.ai.base import BaseAIHandler
    now = now or datetime.utcnow()
    sent = []
    remaining = []
    handler = BaseAIHandler()
    for job in _REVIEW_QUEUE:
        if job['due'] <= now:
            try:
                order = job['order']
                prompt = {
                    'task': 'Generate personalized friendly review request message tailored to customer tone',
                    'order': order,
                    'instructions': 'Return JSON: { message: string }'
                }
                resp = handler.generate(prompt)
                message = None
                if resp.get('ok') and isinstance(resp.get('response'), dict):
                    message = resp['response'].get('message')
                if not message:
                    message = f"Dziękujemy za zakup {order.get('items',[{}])[0].get('product_name','produkt')}. Będziemy wdzięczni za opinię!"
                sent.append({'order_id': job['order_id'], 'message': message})
                _SENT.append({'order_id': job['order_id'], 'message': message, 'ts': datetime.utcnow().isoformat()})
            except Exception:
                logger.exception('Failed to send review for %s', job.get('order_id'))
        else:
            remaining.append(job)

    # replace queue with remaining
    global _REVIEW_QUEUE
    _REVIEW_QUEUE = remaining
    return {'ok': True, 'sent': sent, 'remaining': len(_REVIEW_QUEUE)}


def get_pending_reviews() -> List[Dict[str, Any]]:
    return [{'order_id': j['order_id'], 'due': j['due'].isoformat()} for j in _REVIEW_QUEUE]
