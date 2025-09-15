import httpx
import asyncio
from typing import Dict, Any

async def make_request(method: str, url: str, params=None, headers=None, cookies=None, timeout=15):
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
        try:
            resp = await client.request(method, url, params=params, headers=headers, cookies=cookies)
            return resp
        except Exception as e:
            return None

def normalize_url(base: str, path: str):
    if path.startswith("http"):
        return path
    if base.endswith("/") and path.startswith("/"):
        return base[:-1] + path
    return base + path
