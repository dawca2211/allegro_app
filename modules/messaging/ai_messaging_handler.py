import logging
from typing import Dict, Any
from modules.ai.base import BaseAIHandler

logger = logging.getLogger(__name__)


class MessagingAIHandler(BaseAIHandler):
    def __init__(self, model: str = None, response_mime_type: str = None):
        super().__init__(model=model or 'models/gemini-3-pro-preview', response_mime_type=response_mime_type or 'application/json')

    def analyze_incoming_message(self, message_text: str, lang: str = 'pl') -> Dict[str, Any]:
        """Return sentiment, intent, urgency (1-10) and extracted entities.

        Uses AI to analyze but falls back to heuristics if AI fails.
        """
        prompt = (
            f"Analyze the following customer message and return JSON with keys: sentiment ('negative'|'neutral'|'positive'),"
            f" intent (one of: 'product_question','complaint','shipping_question','price_inquiry','negotiation','other'),"
            f" urgency (1-10), entities (json). Message:\n{message_text}\nReturn JSON."
        )
        resp = self.generate(prompt)
        if not resp.get('ok'):
            logger.error('Messaging analyze AI failed: %s', resp.get('error'))
            # fallback simple heuristics
            text = message_text.lower()
            sentiment = 'negative' if any(w in text for w in ['zły','nie','brak','reklamacja','psuje']) else ('positive' if any(w in text for w in ['dziękuję','super','świetnie']) else 'neutral')
            intent = 'other'
            if any(w in text for w in ['wysył','kiedy wysył','kiedy paczka','tracking']):
                intent = 'shipping_question'
            if any(w in text for w in ['wymiary','rozmiar','wymiary produktu']):
                intent = 'product_question'
            if any(w in text for w in ['cena','taniej','ile kosztuje']):
                intent = 'price_inquiry'
            urgency = 8 if any(w in text for w in ['pilne','natychmiast','teraz']) else 3
            return {'ok': True, 'sentiment': sentiment, 'intent': intent, 'urgency': urgency, 'entities': {}}

        parsed = resp.get('response') or {}
        # expect keys
        return {'ok': True, 'sentiment': parsed.get('sentiment'), 'intent': parsed.get('intent'), 'urgency': parsed.get('urgency'), 'entities': parsed.get('entities', {})}

    def generate_smart_reply(self, message_data: Dict[str, Any], context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an empathetic, human-like reply. If required, trigger integrations.

        message_data: { message_text, sentiment, intent, urgency, entities }
        context_data: { product, order_status, customer_history }
        Returns: { ok, reply_text, action: optional }
        """
        prompt = (
            f"You are a customer support assistant. Use empathetic, human tone. Apply Personal Touch. "
            f"Given incoming message: {message_data} and context: {context_data}, produce JSON: {{'reply_text': string, 'action': optional_object, 'human_required': bool}}"
        )
        resp = self.generate(prompt)
        if not resp.get('ok'):
            logger.error('Messaging reply AI failed: %s', resp.get('error'))
            # fallback generic reply
            reply = "Dziękujemy za wiadomość. Skontaktujemy się wkrótce z odpowiedzią." if context_data.get('lang','pl') == 'pl' else "Thanks for your message. We'll reply shortly."
            return {'ok': False, 'reply_text': reply}

        parsed = resp.get('response') or {}

        # If extreme negative sentiment, flag human
        human_required = False
        if message_data.get('sentiment') == 'negative' and (message_data.get('urgency') or 0) >= 8:
            human_required = True

        result = {
            'ok': True,
            'reply_text': parsed.get('reply_text') or parsed.get('message') or '',
            'action': parsed.get('action'),
            'human_required': parsed.get('human_required', human_required)
        }

        # Integration hooks (best-effort, non-blocking)
        try:
            intent = message_data.get('intent')
            if intent == 'price_inquiry' and parsed.get('action') and isinstance(parsed.get('action'), dict):
                # attempt to call negotiator if requested
                try:
                    from modules.negotiator.negotiator import negotiate
                    # negotiate requires offer_id and many params; attempt with safe defaults
                    offer_id = parsed['action'].get('offer_id') or str(context_data.get('product', {}).get('id'))
                    client_offer = float(parsed['action'].get('client_offer') or message_data.get('entities', {}).get('desired_price') or 0)
                    product = context_data.get('product', {})
                    cust_hist = context_data.get('customer_history', {})
                    inventory = int(context_data.get('inventory_count', 0) or 0)
                    neg = negotiate(offer_id, client_offer, product, cust_hist, inventory, config=parsed['action'].get('config'))
                    result['negotiator_result'] = neg
                except Exception:
                    logger.exception('Negotiate hook failed')
        except Exception:
            logger.exception('Integration hooks failed')

        return result
