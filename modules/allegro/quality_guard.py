from typing import Dict, Any
import logging
import time

from modules.ai.base import BaseAIHandler

logger = logging.getLogger(__name__)


def handle_dispute(dispute_text: str, order_context: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze dispute and return immediate de-escalation reply and suggested resolution.

    Returns: {ok, reply_text, suggested_resolution, human_required}
    """
    handler = BaseAIHandler(response_mime_type='application/json')
    prompt = (
        "You are an expert Allegro seller assistant. Analyze the dispute and propose a calm, conciliatory reply. "
        "Return JSON: { reply_text: string, suggested_resolution: {type: 'refund_partial'|'replace'|'full_refund'|'other', amount: number|null, note: string}, human_required: bool }"
        f"\n\nOrder context: {order_context}\n\nDispute text: {dispute_text}"
    )

    start = time.time()
    resp = handler.generate(prompt)
    elapsed = time.time() - start
    if not resp.get('ok'):
        logger.warning('AI dispute analysis failed: %s', resp.get('error'))
        # fallback simple reply
        reply = 'Przykro nam z powodu problemu. Proponujemy częściowy zwrot lub wymianę — prosimy o potwierdzenie preferencji.'
        return {'ok': True, 'reply_text': reply, 'suggested_resolution': {'type': 'refund_partial', 'amount': None, 'note': 'fallback'}, 'human_required': True, 'elapsed_s': elapsed}

    parsed = resp.get('response') or {}
    return {'ok': True, 'reply_text': parsed.get('reply_text'), 'suggested_resolution': parsed.get('suggested_resolution'), 'human_required': bool(parsed.get('human_required', False)), 'elapsed_s': elapsed}


def monitor_quality_metrics() -> Dict[str, Any]:
    """Monitor shipping times and tracking numbers; proactively prepare messages for delayed shipments.

    Returns a summary of issues detected and actions taken (best-effort).
    """
    # This is a stubbed implementation: in real system we'd query shipments DB / courier APIs
    issues = []
    # Example heuristic: none available -> return ok
    # Provide structure for UI
    return {'ok': True, 'issues': issues, 'note': 'monitoring stub — integrate with shipments DB to activate'}
