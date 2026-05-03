"""
End-to-end test for XSS detection.
Mirrors the exact logic from ExploiterService.try_exploit (GET, XSS branch)
and check_dom_xss without importing the full FastAPI/LLM stack.

Target : http://localhost:9999/mini2/profile?name=
Payload: " autofocus onfocus="alert(document.domain)" x="
"""
import sys
import urllib.parse
import requests

sys.path.insert(0, "app")

from services.playwright_service import check_dom_xss

BASE_URL   = "http://localhost:9999/mini2/profile"
PARAM      = "name"
PAYLOAD    = '" autofocus onfocus="alert(document.domain)" x="'
# Use the exact ZAP alert name to catch alias-mapping bugs
VULN_TYPE  = "User Controllable HTML Element Attribute (Potential XSS)"
COOKIES    = {}
HEADERS    = {}

XSS_TOKENS = ["onfocus", "onerror", "onload", "autofocus", "alert(", "confirm(", "<svg", "<script", "<img"]


def inject_payload(url: str, param: str, payload: str) -> str:
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    qs[param] = payload
    return urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))


# ── Step 1: check_dom_xss in isolation ───────────────────────────────────────
def step1_isolated():
    url = inject_payload(BASE_URL, PARAM, PAYLOAD)
    print(f"\n{'='*60}")
    print("STEP 1 – check_dom_xss (isolated)")
    print(f"URL    : {url}")
    ok, msg = check_dom_xss(url, cookies=COOKIES or None, headless=True)
    print(f"Result : {'✓ DETECTED' if ok else '✗ MISSED'}")
    print(f"Message: {msg}")
    return ok


# ── Step 2: full exploiter logic (reflection check + browser verify) ─────────
def step2_pipeline():
    print(f"\n{'='*60}")
    print("STEP 2 – full exploiter pipeline (reflection → browser verify)")

    test_url = inject_payload(BASE_URL, PARAM, PAYLOAD)
    print(f"URL    : {test_url}")

    # Make the HTTP request exactly like try_exploit does
    response = requests.get(test_url, headers=HEADERS, cookies=COOKIES,
                            verify=False, timeout=15, allow_redirects=True)
    content = response.text.lower()
    print(f"HTTP   : {response.status_code}, body length={len(response.text)}")

    # Reflection check (same logic as exploiter_service.py lines 789-794)
    payload_lower = PAYLOAD.lower()
    tokens_found = [tok for tok in XSS_TOKENS if tok in payload_lower and tok in content]
    payload_reflected = (
        payload_lower in content
        or urllib.parse.quote(payload_lower) in content
        or bool(tokens_found)
    )

    print(f"Tokens found in response: {tokens_found}")
    print(f"Payload reflected: {payload_reflected}")

    if not payload_reflected:
        print("✗ Payload not reflected — server is not echoing the input.")
        return False

    print("[→] Payload reflected. Calling check_dom_xss for browser verification...")
    ok, msg = check_dom_xss(test_url, cookies=COOKIES or None, headless=True)
    print(f"Result : {'✓ VULNERABLE' if ok else '✗ NOT DETECTED'}")
    print(f"Message: {msg}")
    return ok


def main():
    s1 = step1_isolated()
    s2 = step2_pipeline()

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"  check_dom_xss isolated  : {'PASS' if s1 else 'FAIL'}")
    print(f"  full pipeline           : {'PASS' if s2 else 'FAIL'}")
    print('='*60)
    return 0 if (s1 and s2) else 1


if __name__ == "__main__":
    sys.exit(main())
