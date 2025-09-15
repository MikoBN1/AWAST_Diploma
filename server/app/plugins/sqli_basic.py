# checks/sqli_basic.py
import re
from typing import Dict, Any
from common_helpers import make_request

SQL_ERROR_REGEX = [
    r"you have an error in your sql syntax",
    r"unclosed quotation mark after the character string",
    r"SQL syntax.*MySQL",
    r"pg::syntaxerror",
    r"SQL state"
]

async def run(target: str, context: Dict[str, Any]) -> Dict[str, Any]:
    param_candidates = context.get("param_candidates", ["id","user","item","product"])
    headers = context.get("headers")
    cookies = context.get("auth", {}).get("cookies")
    findings = []

    # safe test: inject single quote and look for SQL error strings or notable changes
    for p in param_candidates:
        params = {p: "'"}
        resp = await make_request("GET", target, params=params, headers=headers, cookies=cookies)
        if not resp:
            continue
        body = resp.text.lower() if resp.text else ""
        for pattern in SQL_ERROR_REGEX:
            if re.search(pattern, body, re.IGNORECASE):
                findings.append({
                    "vuln": "sql_injection_error_based",
                    "param": p,
                    "evidence": pattern,
                    "status_code": resp.status_code,
                    "location": str(resp.url)
                })
                break
        # optional: detect large differences in response length (may indicate different query result)
        # but avoid time-based checks in safe mode
        if findings:
            break

    return {"target": target, "findings": findings}
