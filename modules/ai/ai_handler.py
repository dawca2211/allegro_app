import os
import json
import logging
from typing import Dict, Any

# Try to import Google Generative AI SDK
try:
    import google.generativeai as genai
except Exception:
    genai = None


logger = logging.getLogger(__name__)


def call_gemini(prompt: str, model: str = 'models/gemini-3-pro-preview', response_mime_type: str = 'application/json') -> Dict[str, Any]:
    """Call Gemini 3 Pro via google.generativeai. Returns parsed JSON when response_mime_type is JSON.

    Notes: Requires GOOGLE_API_KEY in env.
    """
    if genai is None:
        raise RuntimeError('google.generativeai library not installed. Please install google-generativeai.')

    api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise RuntimeError('GOOGLE_API_KEY not set in environment')

    try:
        # configure client
        genai.configure(api_key=api_key)
        # generate - API shape may vary; using generic call
        response = genai.generate(
            model=model,
            prompt=prompt,
            response_mime_type=response_mime_type
        )

        # Attempt to extract generated content depending on response shape
        # If response_mime_type == 'application/json' we expect response to include JSON text
        text = None
        if hasattr(response, 'text'):
            text = response.text
        else:
            # try common structure
            text = getattr(response, 'content', None) or str(response)

        parsed = None
        if response_mime_type == 'application/json' and text:
            try:
                parsed = json.loads(text)
            except Exception:
                # sometimes response may wrap JSON in choices/candidates
                try:
                    # flatten common fields
                    cand = None
                    if hasattr(response, 'candidates') and len(response.candidates) > 0:
                        cand = response.candidates[0]
                        parsed = json.loads(cand.get('content', cand.get('text', '{}')))
                    elif hasattr(response, 'candidates') and isinstance(response.candidates, list):
                        parsed = json.loads(response.candidates[0]['text'])
                except Exception as e:
                    logger.exception('Failed to parse model JSON response')
                    parsed = {'raw': text}
        else:
            parsed = {'raw': text}

        # log cost metadata when available
        try:
            if hasattr(response, 'metadata'):
                logger.info('Model metadata: %s', getattr(response, 'metadata'))
        except Exception:
            pass

        return {'ok': True, 'response': parsed}

    except Exception as e:
        logger.exception('Gemini call failed')
        return {'ok': False, 'error': str(e)}
