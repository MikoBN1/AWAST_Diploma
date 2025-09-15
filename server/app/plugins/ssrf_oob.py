# checks/ssrf_oob.py
from typing import Dict, Any
from common_helpers import make_request
import urllib.parse

async def run(target: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Context must provide 'collaborator_url' — уникальный URL на вашем OOB сервер (Burp Collaborator, Interactsh, etc.)
    Example: collaborator_url = "uniqueid.oob-server.example"
    """
    param_candidates = context.get("param_candidates", ["url","u","src","image","redirect"])
    collab = context.get("collaborator_url")
    findings = []

    if not collab:
        return {"target": target, "error": "collaborator_url not provided in context", "findings": []}

    # construct a discoverable callback URL (use unique token if possible)
    callback = f"https://{collab}/ptes-{urllib.parse.quote_plus(target)}"

    for p in param_candidates:
        params = {p: callback}
        resp = await make_request("GET", target, params=params, headers=context.get("headers"), cookies=context.get("auth", {}).get("cookies"))
        if not resp:
            continue
        # We cannot observe OOB here — platform should check collaborator logs asynchronously.
        findings.append({
            "vuln": "possible_ssrf_oob",
            "param": p,
            "injected_url": callback,
            "status_code": resp.status_code,
            "note": "Check collaborator server for inbound request. If collaborator saw a hit -> SSRF"
        })
    return {"target": target, "findings": findings}
