import asyncio
import json
import logging
import os
import tempfile
from typing import AsyncGenerator
from urllib.parse import urlparse, parse_qs

from core.config import settings

logger = logging.getLogger(__name__)

_SEVERITY_MAP = {
    "critical": "High",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "info": "Informational",
    "unknown": "Informational",
}


def _extract_param(url: str) -> str | None:
    """Return the first query parameter name found in a URL, or None."""
    try:
        qs = parse_qs(urlparse(url).query)
        return next(iter(qs), None)
    except Exception:
        return None


def normalize_nuclei_finding(finding: dict) -> dict:
    """Map a Nuclei JSON-line finding to the Vulnerability schema dict."""
    info = finding.get("info", {})

    severity_raw = info.get("severity", "unknown").lower()
    risk = _SEVERITY_MAP.get(severity_raw, "Low")

    matched_at = finding.get("matched-at") or finding.get("host", "")

    request_raw = finding.get("request", "")
    method = "GET"
    if request_raw:
        first_line = request_raw.splitlines()[0]
        parts = first_line.split()
        if parts:
            method = parts[0].upper()

    tags_list = info.get("tags", [])
    tags: dict = {t: t for t in tags_list} if isinstance(tags_list, list) else {}

    cwe_ids = info.get("classification", {}).get("cwe-id", [])
    raw_cweid = cwe_ids[0] if cwe_ids else None
    cweid = str(raw_cweid).replace("CWE-", "") if raw_cweid else None

    extracted = finding.get("extracted-results") or []
    payload = extracted[0] if extracted else finding.get("matcher-name") or finding.get("template-id")

    references = info.get("reference") or []
    if isinstance(references, str):
        references = [r.strip() for r in references.splitlines() if r.strip()]

    return {
        "name": info.get("name") or finding.get("template-id", "Unknown"),
        "description": info.get("description", ""),
        "risk": risk,
        "cweid": cweid,
        "url": matched_at,
        "method": method,
        "tags": tags,
        "solution": info.get("remediation"),
        "references": references,
        "parameter": _extract_param(matched_at),
        "payload": payload,
        "request": request_raw,
        "response": finding.get("response", ""),
    }


async def run_nuclei_scan(
    target_url: str,
    urls: list[str] | None = None,
) -> AsyncGenerator[dict, None]:
    """
    Async generator that yields normalized findings as Nuclei discovers them.

    If `urls` is provided (a list of URLs from the ZAP spider), Nuclei is
    pointed at a temporary file containing those URLs via `-list`. Otherwise
    it scans the bare `target_url` with `-u`.
    """
    cmd = [
        settings.NUCLEI_PATH,
        "-json",
        "-silent",
        "-severity", settings.NUCLEI_SEVERITY,
        "-no-interactsh",   # avoid external callbacks in controlled scans
    ]

    tmp_path: str | None = None

    if urls:
        # Write discovered URLs to a temp file and pass via -list
        fd, tmp_path = tempfile.mkstemp(suffix=".txt", prefix="nuclei_urls_")
        try:
            with os.fdopen(fd, "w") as f:
                f.write("\n".join(urls))
            cmd += ["-list", tmp_path]
        except Exception:
            os.close(fd)
            raise
    else:
        cmd += ["-u", target_url]

    logger.info(f"Launching Nuclei: {' '.join(cmd)}")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        assert proc.stdout is not None

        async for raw_line in proc.stdout:
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                finding = json.loads(line)
                yield normalize_nuclei_finding(finding)
            except json.JSONDecodeError:
                logger.debug(f"Nuclei non-JSON output: {line}")

        await proc.wait()

        if proc.returncode not in (0, 1):
            # returncode 1 means "no results", which is fine
            stderr_out = b""
            if proc.stderr:
                stderr_out = await proc.stderr.read()
            logger.warning(
                f"Nuclei exited with code {proc.returncode}: "
                f"{stderr_out.decode('utf-8', errors='replace')[:500]}"
            )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
