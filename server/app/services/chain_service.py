import logging
import uuid
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

SEVERITY_SCORE = {
    "Critical": 10,
    "High": 8,
    "Medium": 5,
    "Low": 2,
    "Informational": 1,
}

VULN_TYPE_MAP = {
    "Cross Site Scripting (Reflected)": "XSS",
    "Cross Site Scripting (Persistent)": "XSS",
    "Cross Site Scripting (DOM Based)": "XSS",
    "Cross Site Scripting": "XSS",
    "SQL Injection": "SQLi",
    "SQL Injection - SQLite": "SQLi",
    "SQL Injection - MySQL": "SQLi",
    "SQL Injection - PostgreSQL": "SQLi",
    "SQL Injection - Oracle": "SQLi",
    "SQL Injection - MsSQL": "SQLi",
    "SQL Injection - Hypersonic SQL": "SQLi",
    "Remote OS Command Injection": "Command Injection",
    "Path Traversal": "Path Traversal",
    "Server Side Request Forgery": "SSRF",
    "XML External Entity Attack": "XXE",
    "External Redirect": "Open Redirect",
    "Server Side Template Injection": "SSTI",
    "Cross-Site Request Forgery (CSRF)": "CSRF",
    "Absence of Anti-CSRF Tokens": "CSRF",
    "Anti-CSRF Tokens Check": "CSRF",
    "Cookie Without Secure Flag": "Cookie Misconfiguration",
    "Cookie No HttpOnly Flag": "Cookie Misconfiguration",
    "X-Frame-Options Header Not Set": "Clickjacking",
    "Content Security Policy (CSP) Header Not Set": "CSP Missing",
    "Missing Anti-clickjacking Header": "Clickjacking",
    "Directory Browsing": "Info Disclosure",
    "Application Error Disclosure": "Info Disclosure",
    "Private IP Disclosure": "Info Disclosure",
    "Information Disclosure - Debug Error Messages": "Info Disclosure",
    "Information Disclosure - Sensitive Information in URL": "Info Disclosure",
}


@dataclass
class NormalizedVuln:
    id: str
    original_name: str
    vuln_type: str
    severity: str
    severity_score: int
    url: str
    method: str
    parameter: str
    cweid: str
    endpoint_path: str
    context_tags: list = field(default_factory=list)


@dataclass
class ChainStep:
    vuln_id: str
    vuln_type: str
    vuln_name: str
    severity: str
    url: str
    parameter: str
    description: str


@dataclass
class AttackChain:
    chain_id: str
    name: str
    description: str
    steps: list
    composite_score: float
    max_impact: str
    affected_endpoints: list
    preconditions: str


# ── Chain rule definitions ────────────────────────────────────────────

CHAIN_RULES = [
    {
        "id": "xss_session_hijack",
        "name": "XSS → Session Hijacking → Account Takeover",
        "description": (
            "Cross-Site Scripting allows injecting malicious scripts that steal session "
            "cookies (especially when HttpOnly is not set), leading to session hijacking "
            "and full account takeover."
        ),
        "required_vulns": ["XSS"],
        "amplifier_vulns": ["Cookie Misconfiguration"],
        "impact": "Critical",
        "preconditions": "Victim must visit a page containing the XSS payload",
        "steps_template": [
            {"vuln_type": "XSS", "description": "Inject malicious JavaScript via reflected or stored XSS vector"},
            {"vuln_type": "Cookie Misconfiguration", "description": "Session cookie lacks HttpOnly flag — accessible to JavaScript", "optional": True},
            {"vuln_type": "_implied", "description": "Exfiltrate session token to attacker-controlled server"},
            {"vuln_type": "_implied", "description": "Replay stolen session cookie to impersonate victim user"},
        ],
    },
    {
        "id": "sqli_data_breach",
        "name": "SQL Injection → Database Dump → Mass Data Breach",
        "description": (
            "SQL Injection enables direct database access, allowing extraction of user "
            "credentials, personal data, and potentially the entire database contents."
        ),
        "required_vulns": ["SQLi"],
        "amplifier_vulns": ["Info Disclosure"],
        "impact": "Critical",
        "preconditions": "Vulnerable SQL endpoint is accessible",
        "steps_template": [
            {"vuln_type": "SQLi", "description": "Exploit SQL injection to execute arbitrary database queries"},
            {"vuln_type": "Info Disclosure", "description": "Error messages reveal database type and schema information", "optional": True},
            {"vuln_type": "_implied", "description": "Enumerate database tables and extract sensitive data (credentials, PII)"},
            {"vuln_type": "_implied", "description": "Use extracted credentials for privilege escalation"},
        ],
    },
    {
        "id": "sqli_auth_bypass",
        "name": "SQL Injection → Authentication Bypass → Admin Access",
        "description": (
            "SQL Injection on authentication endpoints bypasses login entirely, granting "
            "direct access to admin panels and privileged functionality."
        ),
        "required_vulns": ["SQLi"],
        "amplifier_vulns": [],
        "impact": "Critical",
        "preconditions": "SQL Injection exists on or near authentication endpoints",
        "endpoint_hints": ["login", "auth", "signin", "session", "token", "api/auth"],
        "steps_template": [
            {"vuln_type": "SQLi", "description": "Exploit SQL injection to manipulate authentication query logic"},
            {"vuln_type": "_implied", "description": "Bypass login with tautology payload to authenticate as admin"},
            {"vuln_type": "_implied", "description": "Access admin panel and perform privileged operations"},
        ],
    },
    {
        "id": "ssrf_internal_access",
        "name": "SSRF → Internal Service Discovery → Data Exfiltration",
        "description": (
            "Server-Side Request Forgery allows the attacker to make requests from the "
            "server's internal network, accessing cloud metadata, internal APIs, and "
            "sensitive services not exposed to the internet."
        ),
        "required_vulns": ["SSRF"],
        "amplifier_vulns": ["Info Disclosure"],
        "impact": "Critical",
        "preconditions": "Application makes server-side HTTP requests with user-controllable input",
        "steps_template": [
            {"vuln_type": "SSRF", "description": "Forge server-side request to internal network or cloud metadata endpoint"},
            {"vuln_type": "_implied", "description": "Access cloud metadata (e.g., AWS 169.254.169.254) to retrieve IAM credentials"},
            {"vuln_type": "_implied", "description": "Use retrieved credentials to access internal services and extract sensitive data"},
        ],
    },
    {
        "id": "open_redirect_phishing",
        "name": "Open Redirect → Phishing → Credential Theft",
        "description": (
            "Open Redirect on a trusted domain enables convincing phishing attacks by "
            "redirecting users to a malicious lookalike page while the URL appears legitimate."
        ),
        "required_vulns": ["Open Redirect"],
        "amplifier_vulns": [],
        "impact": "High",
        "preconditions": "Attacker crafts a redirect URL pointing to a phishing page",
        "steps_template": [
            {"vuln_type": "Open Redirect", "description": "Craft a URL on the trusted domain that redirects to attacker's phishing page"},
            {"vuln_type": "_implied", "description": "Victim trusts the URL (legitimate domain) and clicks the link"},
            {"vuln_type": "_implied", "description": "Phishing page mimics the login form, capturing entered credentials"},
        ],
    },
    {
        "id": "path_traversal_config_leak",
        "name": "Path Traversal → Configuration Disclosure → System Compromise",
        "description": (
            "Path Traversal allows reading arbitrary files from the server, exposing "
            "configuration files with database credentials, API keys, and internal "
            "architecture details."
        ),
        "required_vulns": ["Path Traversal"],
        "amplifier_vulns": ["Info Disclosure"],
        "impact": "Critical",
        "preconditions": "Server process has read access to sensitive configuration files",
        "steps_template": [
            {"vuln_type": "Path Traversal", "description": "Traverse directory structure to read sensitive config files (.env, web.config)"},
            {"vuln_type": "_implied", "description": "Extract database credentials, API keys, and internal service URLs"},
            {"vuln_type": "_implied", "description": "Use extracted credentials to access database or internal services directly"},
        ],
    },
    {
        "id": "xxe_file_read",
        "name": "XXE → File Read → Internal Network Scanning",
        "description": (
            "XML External Entity injection enables reading local files and making HTTP "
            "requests from the server, mapping the internal network and extracting data."
        ),
        "required_vulns": ["XXE"],
        "amplifier_vulns": ["SSRF"],
        "impact": "Critical",
        "preconditions": "Application processes XML input without disabling external entities",
        "steps_template": [
            {"vuln_type": "XXE", "description": "Inject XML external entity to read local files (/etc/passwd, web.config)"},
            {"vuln_type": "_implied", "description": "Extract configuration files containing credentials and API keys"},
            {"vuln_type": "SSRF", "description": "Use XXE-based SSRF to scan internal network and access metadata", "optional": True},
        ],
    },
    {
        "id": "cmd_injection_rce",
        "name": "Command Injection → Remote Code Execution → Full Compromise",
        "description": (
            "OS Command Injection allows executing arbitrary system commands on the server, "
            "leading to complete system compromise including data theft and lateral movement."
        ),
        "required_vulns": ["Command Injection"],
        "amplifier_vulns": [],
        "impact": "Critical",
        "preconditions": "User input is passed to OS command execution without sanitization",
        "steps_template": [
            {"vuln_type": "Command Injection", "description": "Inject OS command through vulnerable parameter"},
            {"vuln_type": "_implied", "description": "Establish reverse shell or persistent backdoor on the server"},
            {"vuln_type": "_implied", "description": "Escalate privileges and move laterally through the internal network"},
        ],
    },
    {
        "id": "ssti_rce",
        "name": "SSTI → Template Engine Exploitation → Remote Code Execution",
        "description": (
            "Server-Side Template Injection allows executing arbitrary code within the "
            "template engine context, escalating to full remote code execution."
        ),
        "required_vulns": ["SSTI"],
        "amplifier_vulns": ["Info Disclosure"],
        "impact": "Critical",
        "preconditions": "User input is embedded into server-side template without sanitization",
        "steps_template": [
            {"vuln_type": "SSTI", "description": "Inject template syntax to confirm server-side template injection"},
            {"vuln_type": "Info Disclosure", "description": "Error messages reveal template engine type (Jinja2, Twig, etc.)", "optional": True},
            {"vuln_type": "_implied", "description": "Craft engine-specific payload to escape sandbox and execute OS commands"},
            {"vuln_type": "_implied", "description": "Achieve full remote code execution on the server"},
        ],
    },
    {
        "id": "csrf_account_takeover",
        "name": "CSRF → Unauthorized State Changes → Account Takeover",
        "description": (
            "Cross-Site Request Forgery performs state-changing actions on behalf of an "
            "authenticated user, including changing email/password for account takeover."
        ),
        "required_vulns": ["CSRF"],
        "amplifier_vulns": ["XSS"],
        "impact": "High",
        "preconditions": "Victim is authenticated and visits attacker-controlled page",
        "steps_template": [
            {"vuln_type": "CSRF", "description": "Craft a page that triggers state-changing request (change email/password)"},
            {"vuln_type": "XSS", "description": "Use XSS to auto-execute CSRF attack without separate phishing", "optional": True},
            {"vuln_type": "_implied", "description": "Victim's browser sends the forged request to the application"},
            {"vuln_type": "_implied", "description": "Attacker gains access via changed credentials"},
        ],
    },
    {
        "id": "xss_csrf_combo",
        "name": "XSS + CSRF → Self-Propagating Worm → Mass Compromise",
        "description": (
            "Combining XSS with CSRF creates a self-propagating worm: the XSS payload "
            "automatically executes CSRF attacks from every victim's browser, spreading exponentially."
        ),
        "required_vulns": ["XSS", "CSRF"],
        "amplifier_vulns": [],
        "impact": "Critical",
        "preconditions": "Both XSS and CSRF vulnerabilities exist in the same application",
        "steps_template": [
            {"vuln_type": "XSS", "description": "Inject persistent XSS payload that includes CSRF exploit code"},
            {"vuln_type": "CSRF", "description": "CSRF exploit performs critical action (change password, add admin)"},
            {"vuln_type": "_implied", "description": "Each victim who views the XSS payload automatically triggers the CSRF"},
            {"vuln_type": "_implied", "description": "Attack propagates exponentially across all users viewing the page"},
        ],
    },
    {
        "id": "clickjacking_ui_redress",
        "name": "Clickjacking → UI Redressing → Unauthorized Actions",
        "description": (
            "Missing X-Frame-Options allows the application to be embedded in an iframe, "
            "enabling clickjacking attacks that trick users into performing unintended actions."
        ),
        "required_vulns": ["Clickjacking"],
        "amplifier_vulns": ["CSRF", "CSP Missing"],
        "impact": "Medium",
        "preconditions": "Victim visits attacker's page containing hidden iframe of the target",
        "steps_template": [
            {"vuln_type": "Clickjacking", "description": "Embed target application in transparent iframe on attacker's page"},
            {"vuln_type": "CSP Missing", "description": "Lack of Content Security Policy allows unrestricted framing", "optional": True},
            {"vuln_type": "_implied", "description": "Overlay deceptive UI to trick user into clicking hidden buttons"},
            {"vuln_type": "_implied", "description": "User unknowingly performs sensitive actions (transfers, permission changes)"},
        ],
    },
]


# ── Helpers ───────────────────────────────────────────────────────────


def _normalize_vuln_type(name: str) -> str:
    if name in VULN_TYPE_MAP:
        return VULN_TYPE_MAP[name]

    lower = name.lower()
    if "xss" in lower or "cross site scripting" in lower or "cross-site scripting" in lower:
        return "XSS"
    if "sql" in lower and "inject" in lower:
        return "SQLi"
    if "command" in lower and "inject" in lower:
        return "Command Injection"
    if "csrf" in lower or "cross-site request forgery" in lower or "anti-csrf" in lower:
        return "CSRF"
    if "ssrf" in lower or "server side request" in lower:
        return "SSRF"
    if "ssti" in lower or "template injection" in lower:
        return "SSTI"
    if "xxe" in lower or "xml external" in lower:
        return "XXE"
    if "redirect" in lower:
        return "Open Redirect"
    if "traversal" in lower:
        return "Path Traversal"
    if "clickjack" in lower or "x-frame" in lower or "frame-options" in lower:
        return "Clickjacking"
    if "csp" in lower or "content security policy" in lower:
        return "CSP Missing"
    if "httponly" in lower or "secure flag" in lower or "cookie" in lower:
        return "Cookie Misconfiguration"
    if "disclosure" in lower or "information" in lower or "directory" in lower:
        return "Info Disclosure"
    return name


def _extract_endpoint_path(url: str) -> str:
    try:
        return urlparse(url).path.rstrip("/").lower()
    except Exception:
        return url


def _generate_context_tags(vuln_type: str, url: str, parameter: str) -> list:
    tags = []
    path = _extract_endpoint_path(url)
    param_lower = (parameter or "").lower()

    auth_hints = ["login", "auth", "signin", "signup", "register", "password", "session", "token", "oauth"]
    if any(h in path for h in auth_hints) or any(h in param_lower for h in ["pass", "token", "auth"]):
        tags.append("auth_related")
    if "admin" in path or "admin" in param_lower:
        tags.append("admin_endpoint")
    if any(h in path for h in ["user", "profile", "account", "settings"]):
        tags.append("user_data")
    if "/api/" in path or "/v1/" in path or "/v2/" in path:
        tags.append("api_endpoint")
    if any(h in path for h in ["upload", "file", "download", "media"]):
        tags.append("file_access")
    if any(h in path for h in ["pay", "checkout", "order", "cart", "billing"]):
        tags.append("payment")

    return tags


# ── Core algorithm ────────────────────────────────────────────────────


def _normalize_vulnerabilities(alerts: list) -> list[NormalizedVuln]:
    normalized = []
    for idx, alert in enumerate(alerts):
        name = alert.get("name", alert.get("alert", "Unknown"))
        vuln_type = _normalize_vuln_type(name)
        risk = alert.get("risk", "Low")
        url = alert.get("url", "")
        method = alert.get("method", "GET")
        parameter = alert.get("parameter", alert.get("param", ""))
        cweid = str(alert.get("cweid", ""))

        normalized.append(NormalizedVuln(
            id=str(alert.get("id", f"vuln-{idx}")),
            original_name=name,
            vuln_type=vuln_type,
            severity=risk,
            severity_score=SEVERITY_SCORE.get(risk, 1),
            url=url,
            method=method,
            parameter=parameter or "",
            cweid=cweid,
            endpoint_path=_extract_endpoint_path(url),
            context_tags=_generate_context_tags(vuln_type, url, parameter or ""),
        ))
    return normalized


def _discover_chains(normalized_vulns: list[NormalizedVuln]) -> list[AttackChain]:
    vulns_by_type: dict[str, list[NormalizedVuln]] = defaultdict(list)
    for v in normalized_vulns:
        vulns_by_type[v.vuln_type].append(v)

    all_types = set(vulns_by_type.keys())
    discovered: list[AttackChain] = []

    for rule in CHAIN_RULES:
        required = set(rule["required_vulns"])
        if not required.issubset(all_types):
            continue

        if "endpoint_hints" in rule:
            hints = rule["endpoint_hints"]
            primary_type = list(required)[0]
            if not any(
                any(h in v.endpoint_path for h in hints)
                for v in vulns_by_type[primary_type]
            ):
                continue

        amplifiers = set(rule.get("amplifier_vulns", []))
        present_amplifiers = amplifiers.intersection(all_types)

        steps: list[dict] = []
        affected_endpoints: set[str] = set()
        total_severity = 0

        for tmpl in rule["steps_template"]:
            stype = tmpl["vuln_type"]
            is_optional = tmpl.get("optional", False)

            if stype == "_implied":
                steps.append(asdict(ChainStep(
                    vuln_id="implied",
                    vuln_type="implied",
                    vuln_name="Implied Step",
                    severity=rule["impact"],
                    url="",
                    parameter="",
                    description=tmpl["description"],
                )))
            elif stype in vulns_by_type:
                best = max(vulns_by_type[stype], key=lambda v: v.severity_score)
                steps.append(asdict(ChainStep(
                    vuln_id=best.id,
                    vuln_type=best.vuln_type,
                    vuln_name=best.original_name,
                    severity=best.severity,
                    url=best.url,
                    parameter=best.parameter,
                    description=tmpl["description"],
                )))
                affected_endpoints.add(best.url)
                total_severity += best.severity_score
            elif is_optional:
                continue
            else:
                break

        if not steps:
            continue

        amplifier_bonus = len(present_amplifiers) * 1.5
        chain_length_bonus = min(len(steps) * 0.5, 2.0)
        impact_score = SEVERITY_SCORE.get(rule["impact"], 5)
        composite = round(
            (total_severity + impact_score + amplifier_bonus + chain_length_bonus)
            / max(len(steps), 1) * 2,
            1,
        )
        composite = min(composite, 10.0)

        discovered.append(AttackChain(
            chain_id=str(uuid.uuid4()),
            name=rule["name"],
            description=rule["description"],
            steps=steps,
            composite_score=composite,
            max_impact=rule["impact"],
            affected_endpoints=list(affected_endpoints),
            preconditions=rule["preconditions"],
        ))

    discovered.sort(key=lambda c: c.composite_score, reverse=True)
    return discovered


# ── Public service ────────────────────────────────────────────────────


class ChainAnalysisService:
    """Analyzes vulnerability scan results to discover multi-step attack chains."""

    def analyze(self, alerts: list[dict]) -> dict:
        normalized = _normalize_vulnerabilities(alerts)
        chains = _discover_chains(normalized)

        vuln_type_counts: dict[str, int] = defaultdict(int)
        for v in normalized:
            vuln_type_counts[v.vuln_type] += 1

        severity_counts: dict[str, int] = defaultdict(int)
        for c in chains:
            severity_counts[c.max_impact] += 1

        endpoint_chain_count: dict[str, int] = defaultdict(int)
        for c in chains:
            for ep in c.affected_endpoints:
                endpoint_chain_count[ep] += 1

        most_chained = sorted(
            endpoint_chain_count.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "total_vulnerabilities": len(normalized),
            "total_chains_discovered": len(chains),
            "chains": [asdict(c) for c in chains],
            "summary": {
                "by_impact": dict(severity_counts),
                "vuln_type_distribution": dict(vuln_type_counts),
                "most_chained_endpoints": [
                    {"url": url, "chain_count": cnt} for url, cnt in most_chained
                ],
                "highest_score": chains[0].composite_score if chains else 0,
            },
        }
