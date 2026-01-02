from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def _safe_import(name: str, attr: str = None):
    try:
        mod = __import__(name, fromlist=[attr] if attr else [])
        return getattr(mod, attr) if attr else mod
    except Exception:
        logger.exception('Optional import failed: %s.%s', name, attr)
        return None


def analyze_discussion(discussion: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a buyer-seller discussion and propose a prioritized reply.

    discussion: {id, order_id, messages: [{from, text, ts}], buyer_history: {...}}
    Returns: {ok, priority, suggested_reply, human_required}
    """
    BaseAIHandler = _safe_import('modules.ai.base', 'BaseAIHandler')
    if BaseAIHandler is None:
        # fallback heuristics
        text = ' '.join(m.get('text','') for m in discussion.get('messages',[])).lower()
        urgency = 'high' if any(w in text for w in ['reklamacja','pilne','natychmiast','pilsne','uszkodzon']) else 'medium'
        reply = 'Dziękujemy za zgłoszenie. Pracujemy nad sprawą i wrócimy w ciągu 1 godziny.'
        return {'ok': True, 'priority': urgency, 'suggested_reply': reply, 'human_required': False}

    handler = BaseAIHandler(response_mime_type='application/json')
    prompt = {
        'task': 'Prioritize and draft a de-escalating reply for an Allegro discussion. Fast response <1h.',
        'discussion': discussion,
        'instructions': 'Return JSON: { priority: "high|medium|low", suggested_reply: string, human_required: bool }'
    }
    resp = handler.generate(prompt)
    if not resp.get('ok'):
        logger.warning('AI quality analysis failed: %s', resp.get('error'))
        return {'ok': False, 'error': resp.get('error')}

    parsed = resp.get('response') or {}
    return {'ok': True, 'priority': parsed.get('priority','medium'), 'suggested_reply': parsed.get('suggested_reply','Dziękujemy, sprawdzamy.'), 'human_required': bool(parsed.get('human_required', False))}


def prioritize_discussions(discussions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for d in discussions:
        try:
            r = analyze_discussion(d)
            out.append({'discussion_id': d.get('id'), 'priority': r.get('priority'), 'human_required': r.get('human_required'), 'suggested_reply': r.get('suggested_reply')})
        except Exception:
            logger.exception('Failed to analyze discussion %s', d.get('id'))
            out.append({'discussion_id': d.get('id'), 'priority': 'medium', 'human_required': True, 'suggested_reply': ''})
    # sort high->low
    order = {'high': 0, 'medium': 1, 'low': 2}
    return sorted(out, key=lambda x: order.get(x.get('priority','medium'), 1))
