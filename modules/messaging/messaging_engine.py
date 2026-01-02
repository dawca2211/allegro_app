from typing import Dict, Any
from modules.messaging.ai_messaging_handler import MessagingAIHandler
import logging

logger = logging.getLogger(__name__)


handler = MessagingAIHandler()


def analyze_incoming_message(message_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    context = context or {}
    return handler.analyze_incoming_message(message_text, lang=context.get('lang','pl'))


def generate_smart_reply(message_data: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper around handler.generate_smart_reply that also enriches context (order status stub).
    """
    # enrich context with order status if order_id present (stub)
    if context_data and context_data.get('order_id'):
        # stubbed order status
        context_data.setdefault('order_status', {'status': 'shipped', 'eta': '2 dni'})

    return handler.generate_smart_reply(message_data, context_data)
