import asyncio
import httpx

async def main():
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get('http://localhost:8080/JSON/spider/action/scan/', params={'apikey': 'changeme', 'url': 'http://example.com/'})
            print(resp.status_code)
            print(resp.json())
    except Exception as e:
        print("Error:", type(e), e)

asyncio.run(main())
