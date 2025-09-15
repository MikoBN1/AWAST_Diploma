from typing import Dict, Any
from plugins.common_helpers import make_request

MARKER = "<PTES_XSS_TEST>"

async def run(target: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    target: base url (e.g. https://example.com/search)
    context: { safe_mode: bool, auth: {...}, param_candidates: [...], headers: {...} }
    """
    param_candidates = context.get("param_candidates", ["q","search","term","s"])
    headers = context.get("headers")
    cookies = context.get("auth", {}).get("cookies")
    results = []

    for p in param_candidates:
        params = {p: MARKER}
        resp = await make_request("GET", target, params=params, headers=headers, cookies=cookies)
        if not resp:
            continue
        body = resp.text or ""
        # detection: simple substring reflection
        if MARKER in body:
            results.append({
                "vuln": "reflected_xss",
                "param": p,
                "evidence": MARKER,
                "status_code": resp.status_code,
                "location": str(resp.url)
            })
            # stop early on positive found
            break

    return {"target": target, "findings": results, "safe_mode": context.get("safe_mode", True)}
