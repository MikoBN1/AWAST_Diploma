# checks/idor_enum.py
import asyncio
from typing import Dict, Any
from common_helpers import make_request
from difflib import SequenceMatcher

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

async def run(base_url_template: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    base_url_template: e.g. "https://example.com/api/documents/{id}"
    context: {
      safe_mode: bool,
      auth: {...},
      start_id: 100,
      max_enum: 5
    }
    """
    start = context.get("start_id", 1)
    max_enum = context.get("max_enum", 5)
    headers = context.get("headers")
    cookies = context.get("auth", {}).get("cookies")
    findings = []

    # fetch baseline (start)
    url0 = base_url_template.format(id=start)
    resp0 = await make_request("GET", url0, headers=headers, cookies=cookies)
    if not resp0:
        return {"target_template": base_url_template, "error": "no baseline response", "findings": []}
    body0 = resp0.text or ""
    code0 = resp0.status_code

    # iterate nearby ids
    for i in range(1, max_enum+1):
        for cand in (start + i, start - i):
            if cand <= 0:
                continue
            url = base_url_template.format(id=cand)
            resp = await make_request("GET", url, headers=headers, cookies=cookies)
            if not resp:
                continue
            body = resp.text or ""
            code = resp.status_code
            sim = similarity(body0, body)
            # heuristics: different content but accessible (200) may indicate other user's object
            if code == 200 and sim < 0.9:
                findings.append({
                    "vuln": "possible_idor",
                    "id_tested": cand,
                    "baseline_id": start,
                    "similarity": sim,
                    "evidence_snippet": body[:500],
                    "url": str(resp.url)
                })
    return {"target_template": base_url_template, "findings": findings}
