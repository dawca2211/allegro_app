from typing import Dict, Any
from modules.finance.calculator import calculate_margin
from modules.negotiator.ai_negotiator_handler import ask_negotiator_ai


MIN_MARGIN_PCT = 0.10


def get_min_price_for_product(product: Dict[str, Any], config: Dict[str, Any] = None) -> float:
    """Calculate minimal acceptable price based on product costs and MIN_MARGIN_PCT.
    Uses calculator components: cost, packaging, shipping, ads, marketplace_fee_pct
    """
    product_costs = {
        'cost': float(product.get('cost', 0)),
        'packaging': float(product.get('packaging_cost', 0)),
        'shipping': float(product.get('shipping_cost', 0)),
        'ads': float(product.get('ads_cost', 0))
    }
    marketplace_fees = {'fee_pct': float(product.get('marketplace_fee_pct', 0.15))}
    # find minimal sale price that yields MIN_MARGIN_PCT
    # solve for sale_price in (sale_price - total_costs)/sale_price >= MIN_MARGIN_PCT
    # total_costs = fixed_costs + sale_price * fee_pct
    fixed_costs = product_costs['cost'] + product_costs['packaging'] + product_costs['shipping'] + product_costs['ads']
    fee_pct = marketplace_fees['fee_pct']
    # margin = (p - fixed_costs - p*fee_pct)/p = 1 - fee_pct - (fixed_costs / p) >= MIN_MARGIN_PCT
    # => 1 - fee_pct - MIN_MARGIN_PCT >= fixed_costs / p
    # => p >= fixed_costs / (1 - fee_pct - MIN_MARGIN_PCT)
    denom = (1 - fee_pct - MIN_MARGIN_PCT)
    if denom <= 0:
        # can't reach margin with current fees; fallback to cost* (1+MIN_MARGIN_PCT)
        return round(product_costs['cost'] * (1 + MIN_MARGIN_PCT), 2)
    min_price = fixed_costs / denom
    return round(max(min_price, product_costs['cost'] * (1 + MIN_MARGIN_PCT)), 2)


def negotiate(offer_id: str, client_offer: float, product: Dict[str, Any], customer_history: Dict[str, Any], inventory_count: int, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Run negotiation flow: call AI, validate with calculator, and return final decision.

    Returns: { decision, message, proposed_price, reason }
    """
    # compute our minimal price
    min_price = get_min_price_for_product(product, config=config)

    # build payload for AI
    payload = {
        'client_offer': client_offer,
        'product': product,
        'min_price': min_price,
        'customer_history': customer_history,
        'inventory_count': inventory_count,
        'config': config or {}
    }

    ai_resp = ask_negotiator_ai(payload)
    if not ai_resp.get('ok'):
        return {'decision': 'REJECT', 'message': 'AI error', 'error': ai_resp.get('error')}

    decision_obj = ai_resp.get('decision') or {}
    # expect structure: { decision, proposed_price, reason, message, actions }
    decision = decision_obj.get('decision')
    proposed_price = decision_obj.get('proposed_price')

    # Validate proposed price via calculator
    if proposed_price is not None:
        product_costs = {
            'cost': float(product.get('cost', 0)),
            'packaging': float(product.get('packaging_cost', 0)),
            'shipping': float(product.get('shipping_cost', 0)),
            'ads': float(product.get('ads_cost', 0))
        }
        marketplace_fees = {'fee_pct': float(product.get('marketplace_fee_pct', 0.15))}
        margin = calculate_margin(float(proposed_price), product_costs, marketplace_fees)
        if margin < (config.get('min_margin_pct', 0.10) if config else MIN_MARGIN_PCT):
            # reject unsupported low offer, ask AI to produce safe counter
            return {'decision': 'REJECT', 'message': 'Proposed price below minimal margin', 'proposed_price': proposed_price, 'reason': decision_obj.get('reason')}
        else:
            return {'decision': decision or 'COUNTER_OFFER', 'message': decision_obj.get('message'), 'proposed_price': proposed_price, 'reason': decision_obj.get('reason')}

    # No proposed price -> return decision as-is
    return {'decision': decision or 'REJECT', 'message': decision_obj.get('message'), 'reason': decision_obj.get('reason')}
