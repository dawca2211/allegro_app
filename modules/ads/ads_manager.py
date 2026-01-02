from typing import Dict, Any
import logging

from modules.finance.calculator import calculate_margin

logger = logging.getLogger(__name__)


def adjust_ads_based_on_margin(product_id: str, current_margin: float, product_info: Dict[str, Any] = None, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Decide ad action based on margin and product performance.

    Returns: {ok, action: 'LOWER_CPC'|'PAUSE_ADS'|'BOOST_ADS'|None, reason}
    """
    cfg = config or {}
    pause_threshold = float(cfg.get('pause_margin_pct', 0.07))
    boost_threshold = float(cfg.get('boost_margin_pct', 0.20))

    try:
        m = float(current_margin)
    except Exception:
        logger.exception('Invalid margin value for %s', product_id)
        return {'ok': False, 'error': 'invalid_margin'}

    # If margin dangerously low, pause ads
    if m < pause_threshold:
        reason = f'margin {m} < pause_threshold {pause_threshold}'
        logger.info('AdsManager: PAUSE_ADS for %s: %s', product_id, reason)
        return {'ok': True, 'action': 'PAUSE_ADS', 'reason': reason}

    # If margin moderate low, lower CPC
    if m < (pause_threshold + 0.05):
        reason = f'margin {m} low — lower CPC'
        logger.info('AdsManager: LOWER_CPC for %s: %s', product_id, reason)
        return {'ok': True, 'action': 'LOWER_CPC', 'reason': reason}

    # If margin high and product_info suggests good conversion, boost
    conv = float(product_info.get('conversion_rate', 0) or 0) if product_info else 0
    if m >= boost_threshold and conv >= 0.02:
        reason = f'high margin {m} and conv {conv} — boost ads'
        logger.info('AdsManager: BOOST_ADS for %s: %s', product_id, reason)
        return {'ok': True, 'action': 'BOOST_ADS', 'reason': reason}

    return {'ok': True, 'action': None, 'reason': 'no_change'}
