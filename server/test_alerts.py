import asyncio
import httpx
from core.config import settings

async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Get active scans to find a valid scanId
        resp = await client.get(
            f"{settings.ZAP_API_URL}/JSON/ascan/view/scans/",
            params={"apikey": settings.ZAP_API_KEY}
        )
        scans = resp.json().get('scans', [])
        print("Scans:", scans)
        if scans:
            scan_id = scans[-1]['id']
            # Get alerts by scan ID
            ids_resp = await client.get(
                f"{settings.ZAP_API_URL}/JSON/ascan/view/alertsIds/",
                params={"apikey": settings.ZAP_API_KEY, "scanId": scan_id}
            )
            print("Alerts IDs:", ids_resp.json())
            
            alerts_ids = ids_resp.json().get('alertsIds', [])
            if alerts_ids:
                # print the first one
                first_id = alerts_ids[0]
                alert_resp = await client.get(
                    f"{settings.ZAP_API_URL}/JSON/core/view/alert/",
                    params={"apikey": settings.ZAP_API_KEY, "id": first_id}
                )
                print("Alert detail:", alert_resp.json())

if __name__ == "__main__":
    asyncio.run(main())
