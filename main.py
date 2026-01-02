from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from typing import List, Dict, Any, Optional

from prompts import AGENT_PERSONA, REPRICING_PROMPT_TEMPLATE, REPRICING_PROMPT_BRIEF
from modules.repricing.repricer import compute_new_price, fetch_competitor_prices, enforce_margin_or_adjust
from modules.ai.ai_handler import call_gemini
from modules.finance.calculator import calculate_margin

# try to import optional helpers
try:
    import ebay_auth
except Exception:
    ebay_auth = None
try:
    import google_drive_manager
except Exception:
    google_drive_manager = None

app = FastAPI()
MODEL_NAME = os.environ.get('LM_MODEL', 'models/gemini-3-pro-preview')

# Simple LM client stub - replace with actual Gemini/OpenAI client code

def send_to_model(prompt: str, model_name: str = MODEL_NAME) -> Dict[str, Any]:
    """Call configured LM (Gemini) via ai_handler and return structured response.

    Falls back to stub response if model call fails.
    """
    try:
        resp = call_gemini(prompt, model=model_name, response_mime_type='application/json')
        return resp
    except Exception as e:
        return {'ok': False, 'error': str(e), 'model': model_name}


class ProductIn(BaseModel):
    id: str
    sku: Optional[str]
    price: float
    cost: float
    our_lead_time_days: Optional[float] = 1
    our_rating: Optional[float] = 5.0


class CompetitorIn(BaseModel):
    seller: str
    price: float
    lead_time_days: Optional[float] = 5
    rating: Optional[float] = 4.5


class RepriceRequest(BaseModel):
    product: ProductIn
    competitors: Optional[List[CompetitorIn]] = None
    competitor_sources: Optional[List[Dict[str, Any]]] = None
    config: Optional[Dict[str, Any]] = None


@app.post('/api/reprice')
async def reprice(req: RepriceRequest):
    # get competitor prices either from payload or by fetching sources
    competitors = []
    if req.competitors:
        competitors = [c.dict() for c in req.competitors]
    elif req.competitor_sources:
        competitors = fetch_competitor_prices(req.competitor_sources)

    product = req.product.dict()
    result = compute_new_price(product, competitors, config=req.config)
    return result


@app.post('/api/reprice_with_model')
async def reprice_with_model(req: RepriceRequest):
    # build a prompt for the model
    competitors = [c.dict() for c in req.competitors] if req.competitors else fetch_competitor_prices(req.competitor_sources or [])
    prompt = REPRICING_PROMPT_TEMPLATE.format(persona=AGENT_PERSONA)
    brief = REPRICING_PROMPT_BRIEF.format(persona=AGENT_PERSONA, product=req.product.json(), competitors=str(competitors), config=str(req.config or {}))
    full = prompt + "\n\n" + brief

    # Call the LM (Gemini)
    lm_resp = send_to_model(full, MODEL_NAME)

    # Also compute deterministic recommendation
    deterministic = compute_new_price(req.product.dict(), competitors, config=req.config)

    return {
        'lm': lm_resp,
        'deterministic': deterministic
    }


@app.post('/api/execute_repricing')
async def execute_repricing(req: RepriceRequest):
    # 1) gather competitors
    competitors = [c.dict() for c in req.competitors] if req.competitors else fetch_competitor_prices(req.competitor_sources or [])

    # 2) deterministic baseline
    deterministic = compute_new_price(req.product.dict(), competitors, config=req.config)

    # 3) prepare prompt for Gemini including competitor data
    brief = REPRICING_PROMPT_BRIEF.format(persona=AGENT_PERSONA, product=req.product.json(), competitors=str(competitors), config=str(req.config or {}))
    prompt = REPRICING_PROMPT_TEMPLATE.format(persona=AGENT_PERSONA) + "\n\n" + brief

    # 4) ask model
    lm_resp = send_to_model(prompt, MODEL_NAME)

    # 5) parse model suggestion
    suggested_price = None
    if lm_resp.get('ok') and isinstance(lm_resp.get('response'), dict):
        suggested_price = lm_resp['response'].get('new_price')

    # 6) enforce margin using calculator
    final = {
        'deterministic': deterministic,
        'lm': lm_resp,
        'final_price': None,
        'final_reason': None,
        'margin_ok': None
    }

    # prefer model suggestion if safe
    candidate = deterministic['new_price']
    if suggested_price is not None:
        candidate = float(suggested_price)

    enforcement = enforce_margin_or_adjust(candidate, req.product.dict(), config=req.config)
    final['final_price'] = enforcement['safe_price']
    final['margin_ok'] = enforcement['ok']
    final['final_reason'] = f"chosen_candidate={candidate}; margin={enforcement['margin']}";

    # if margin not ok and deterministic differs, fallback to deterministic safe price
    if not enforcement['ok'] and deterministic.get('new_price') is not None:
        fallback_enf = enforce_margin_or_adjust(deterministic['new_price'], req.product.dict(), config=req.config)
        final['final_price'] = fallback_enf['safe_price']
        final['final_reason'] += f"; fallback_to_deterministic={fallback_enf['safe_price']}"

    return final


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
