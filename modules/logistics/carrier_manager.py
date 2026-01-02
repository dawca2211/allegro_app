from typing import Dict, Any, List
import logging
from modules.ai.base import BaseAIHandler

logger = logging.getLogger(__name__)


_ai = BaseAIHandler()


def select_optimal_carrier(package_data: Dict[str, Any], destination: Dict[str, Any], carriers: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Select best carrier given package and destination.

    package_data: {weight_kg, dimensions: {l,w,h}, value}
    destination: {country, postcode, region}
    carriers: optional list of carriers with c{'name','base_price','price_per_kg','lead_time_days','reliability' (0-1)}

    Returns: {carrier_name, estimated_cost, estimated_lead_time, reason}
    """
    # default stub carriers
    if carriers is None:
        carriers = [
            {'name': 'DHL', 'base_price': 10.0, 'price_per_kg': 3.0, 'lead_time_days': 2, 'reliability': 0.98},
            {'name': 'InPost', 'base_price': 6.0, 'price_per_kg': 2.5, 'lead_time_days': 3, 'reliability': 0.95},
            {'name': 'LocalCourier', 'base_price': 4.0, 'price_per_kg': 2.0, 'lead_time_days': 5, 'reliability': 0.9}
        ]

    weight = float(package_data.get('weight_kg', 1.0))
    value = float(package_data.get('value', 0))

    # try to ask AI for recommendation (non-blocking fallback)
    ai_prompt = f"Select optimal carrier for package {package_data} to {destination}. Available carriers: {carriers}. Return JSON with keys: carrier, cost, lead_time, reason." 
    ai_resp = _ai.generate(ai_prompt)
    if ai_resp.get('ok') and isinstance(ai_resp.get('response'), dict):
        try:
            resp = ai_resp.get('response')
            return {'carrier_name': resp.get('carrier'), 'estimated_cost': resp.get('cost'), 'estimated_lead_time': resp.get('lead_time'), 'reason': resp.get('reason'), 'source': 'ai'}
        except Exception:
            logger.exception('AI carrier parse failed; falling back')

    # deterministic scoring: lower cost better, lower lead_time better, higher reliability better
    scored = []
    for c in carriers:
        cost = c['base_price'] + c['price_per_kg'] * weight
        lead = c['lead_time_days']
        reliability = c.get('reliability', 0.9)
        # score: normalized: lower is better
        score = cost * 0.6 + lead * 1.5 - reliability * 10
        scored.append((score, c, cost, lead))

    scored.sort(key=lambda x: x[0])
    best = scored[0]
    carrier = best[1]
    return {'carrier_name': carrier['name'], 'estimated_cost': round(best[2], 2), 'estimated_lead_time': int(best[3]), 'reason': 'deterministic_score', 'source': 'deterministic'}
