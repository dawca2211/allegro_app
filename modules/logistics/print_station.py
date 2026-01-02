from typing import Dict, Any, List
import logging
from modules.ai.base import BaseAIHandler

logger = logging.getLogger(__name__)

_ai = BaseAIHandler()


def generate_packing_slip(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a smart packing slip optimized for shortest walk-through.

    order_data expected to contain 'order_id', 'items': [{sku, qty, product_name, location}],
    where location is a string like 'A/12/3' or coordinates.
    """
    items = order_data.get('items', [])
    if not items:
        return {'order_id': order_data.get('order_id'), 'packing_list': [], 'note': 'no items'}

    # Prepare a prompt for AI to order items for efficient picking
    try:
        prompt = {
            'task': 'Order items for shortest warehouse route',
            'order_id': order_data.get('order_id'),
            'items': items
        }
        ai_result = _ai.generate(prompt)
        if ai_result.get('ok') and isinstance(ai_result.get('response'), dict):
            out = ai_result.get('response')
            out.setdefault('order_id', order_data.get('order_id'))
            out.setdefault('packing_list', out.get('packing_list', items))
            out.setdefault('note', 'sorted by AI')
            return out
    except Exception:
        logger.exception('AI packing slip failed, falling back')

    # Fallback: sort by location string
    sorted_items = sorted(items, key=lambda it: str(it.get('location', '')))
    packing_list = []
    for it in sorted_items:
        packing_list.append({'sku': it.get('sku'), 'qty': it.get('qty', 1), 'location': it.get('location'), 'name': it.get('product_name')})

    return {'order_id': order_data.get('order_id'), 'packing_list': packing_list, 'note': 'sorted_by_location'}


def group_print_batch(orders: List[Dict[str, Any]], group_by: str = 'carrier') -> Dict[str, List[Dict[str, Any]]]:
    """Group orders into print batches. group_by: 'carrier' or 'product'
    Returns mapping: key -> list of print jobs (packing slips + labels)
    """
    batches: Dict[str, List[Dict[str, Any]]] = {}
    for order in orders:
        key = 'unknown'
        if group_by == 'carrier':
            key = order.get('preferred_carrier') or order.get('carrier') or 'other'
        elif group_by == 'product':
            # group by first product sku
            items = order.get('items', [])
            key = items[0]['sku'] if items else 'other'

        batches.setdefault(key, []).append(order)

    # for each batch, prepare small print manifest
    manifests: Dict[str, List[Dict[str, Any]]] = {}
    for k, v in batches.items():
        jobs = []
        for o in v:
            slip = generate_packing_slip(o)
            # stub label generator data
            label = {
                'order_id': o.get('order_id'),
                'to': o.get('shipping_to'),
                'carrier': o.get('preferred_carrier') or o.get('carrier'),
            }
            jobs.append({'packing_slip': slip, 'label': label})
        manifests[k] = jobs

    return manifests
