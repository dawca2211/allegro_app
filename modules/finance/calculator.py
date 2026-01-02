from typing import Dict, Any


def calculate_margin(sale_price: float, product_costs: Dict[str, float], marketplace_fees: Dict[str, float]) -> float:
    """Calculate net margin as (sale_price - total_costs) / sale_price.

    product_costs: { cost, packaging, shipping, ads }
    marketplace_fees: { fee_pct } e.g. 0.15 for 15%
    Returns margin as fraction (0.2 = 20%)
    """
    cost = float(product_costs.get('cost', 0))
    packaging = float(product_costs.get('packaging', 0))
    shipping = float(product_costs.get('shipping', 0))
    ads = float(product_costs.get('ads', 0))
    fee_pct = float(marketplace_fees.get('fee_pct', 0))

    # marketplace fee applies to sale price
    marketplace_fee = sale_price * fee_pct

    total_costs = cost + packaging + shipping + ads + marketplace_fee
    margin = (sale_price - total_costs) / sale_price if sale_price > 0 else 0
    return margin
