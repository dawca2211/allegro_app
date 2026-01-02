from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def check_and_flag_ads(sku: str, margin: float, threshold: float = 0.05) -> Dict[str, Any]:
    """Check margin and return PAUSE_ADS flag if below threshold."""
    try:
        m = float(margin)
    except Exception:
        logger.exception('Invalid margin for SKU %s', sku)
        return {'ok': False, 'error': 'invalid_margin'}

    if m < threshold:
        reason = f'margin_below_threshold ({m} < {threshold})'
        # In real system we'd call ad platform API to pause campaigns
        logger.info('Flagging PAUSE_ADS for %s: %s', sku, reason)
        return {'ok': True, 'flag': 'PAUSE_ADS', 'sku': sku, 'reason': reason}

    return {'ok': True, 'flag': None}


def evaluate_product_for_ads(product: Dict[str, Any], margin: float, config: Dict[str, Any] = None) -> Dict[str, Any]:
    cfg = config or {}
    threshold = float(cfg.get('min_margin_pct_for_ads', 0.05))
    return check_and_flag_ads(product.get('sku') or product.get('id'), margin, threshold=threshold)
