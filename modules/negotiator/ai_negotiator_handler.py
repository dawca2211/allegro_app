import logging
from typing import Dict, Any
from modules.ai.ai_handler import call_gemini
from prompts import MODULE_PROMPTS

logger = logging.getLogger(__name__)


def ask_negotiator_ai(payload: Dict[str, Any], model: str = 'models/gemini-3-pro-preview') -> Dict[str, Any]:
    """Call Gemini with negotiator prompt and return parsed decision.

    payload should contain: client_offer, product, min_price, customer_history, inventory_count, config
    """
    prompt_template = MODULE_PROMPTS.get('negocjator')
    if not prompt_template:
        raise RuntimeError('Negociator prompt not found')

    prompt = prompt_template.format(persona=payload.get('persona') or '') + "\n\n" + str(payload)

    try:
        resp = call_gemini(prompt, model=model, response_mime_type='application/json')
        if not resp.get('ok'):
            logger.error('AI negociator failed: %s', resp.get('error'))
            return {'ok': False, 'error': resp.get('error')}
        return {'ok': True, 'decision': resp.get('response')}
    except Exception as e:
        logger.exception('Negociator call exception')
        return {'ok': False, 'error': str(e)}
