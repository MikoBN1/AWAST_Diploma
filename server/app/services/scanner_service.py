import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_cancelled_scans: Set[str] = set()

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.scan_model import Scan
from models.vulnerability_model import Vulnerability
from schemas.report_schema import Vulnerability as VulnerabilitySchema
from services.database_service import AsyncDatabaseService
from services.websocket_service import manager

# ZAP Confidence mapping: 0=Low, 1=Medium, 2=High
CONFIDENCE_MAP = {
    "Low": "0",
    "Medium": "1",
    "High": "2"
}

async def _zap_get(client: httpx.AsyncClient, url: str, params: dict) -> dict:
    resp = await client.get(url, params=params)
    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError:
        try:
            msg = resp.json().get("message", resp.text)
        except Exception:
            msg = resp.text
        raise HTTPException(status_code=400, detail=f"ZAP API Error: {msg}")
    return resp.json()


async def _setup_zap_session(
    client: httpx.AsyncClient,
    cookies: Dict[str, str],
) -> None:
    """Inject authentication cookies into ZAP via Replacer add-on."""
    # [SECURITY FIRST: Защита от пустых данных]
    if not cookies:
        logger.warning("No cookies provided to _setup_zap_session. Scanning unauthenticated!")
        return

    cookie_string = "; ".join(f"{k}={v}" for k, v in cookies.items())
    rule_description = "AWAST_AUTH_COOKIES"

    logger.info(f"Attempting to set ZAP cookies: {cookie_string}")

    # 1. Удаляем старое правило (если есть), чтобы избежать конфликтов
    try:
        await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/replacer/action/removeRule/",
            {"apikey": settings.ZAP_API_KEY, "description": rule_description},
        )
    except HTTPException:
        # Ошибка 400 здесь - норма (правила просто не было)
        pass

    # 2. Создаем новое правило с жестким контролем ошибок
    try:
        response = await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/replacer/action/addRule/",
            {
                "apikey": settings.ZAP_API_KEY,
                "description": rule_description,
                "enabled": "true",
                "matchType": "REQ_HEADER",
                "matchRegex": "false",
                "matchString": "Cookie",
                "replacement": cookie_string,
            },
        )
        logger.info(f"ZAP Replacer successfully created rule: {response}")
    except Exception as e:
        # [SECURITY FIRST: Логируем критический сбой аутентификации]
        logger.error(f"CRITICAL: Failed to inject cookies into ZAP. Scanner will be unauthenticated! Error: {e}")
        raise  # Лучше прервать скан, чем сканировать без авторизации и получить ложные результаты

async def start_spider(
    target: str, cookies: Optional[Dict[str, str]] = None
) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        if cookies:
            try:
                await _setup_zap_session(client, cookies)
            except Exception as e:
                logger.warning(f"Failed to setup ZAP session for spider: {e}")
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/spider/action/scan/",
            {"apikey": settings.ZAP_API_KEY, "url": target}
        )


async def get_spider_status(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/spider/view/status/",
            {"apikey": settings.ZAP_API_KEY, "scanId": scan_id}
        )


async def stop_spider(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/spider/action/stop/",
            {"apikey": settings.ZAP_API_KEY, "scanId": scan_id}
        )

async def start_scan(
    target: str,
    user_id: str,
    db: AsyncSession,
    cookies: Optional[Dict[str, str]] = None,
) -> dict:
    database_service = AsyncDatabaseService(lambda: db)
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Inject auth cookies into ZAP via Replacer if provided
        if cookies:
            try:
                await _setup_zap_session(client, cookies)
            except Exception as e:
                logger.warning(f"Failed to setup ZAP session for {target}: {e}")

        # Fast mode: lower attack strength for all policies to reduce load and speed up scanning
        try:
            policies_resp = await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/ascan/view/policies/",
                {"apikey": settings.ZAP_API_KEY},
            )
            for policy in policies_resp.get("policies", []):
                policy_id = policy.get("id")
                if policy_id is None:
                    continue
                await _zap_get(
                    client,
                    f"{settings.ZAP_API_URL}/JSON/ascan/action/setPolicyAttackStrength/",
                    {
                        "apikey": settings.ZAP_API_KEY,
                        "id": str(policy_id),
                        "attackStrength": "HIGH",
                    },
                )
            logger.info("ZAP Attack Strength set to HIGH for all policies (Fast Mode)")
        except Exception as e:
            logger.warning(f"Failed to set Attack Strength to HIGH: {e}")

        # [SECURITY FIRST: 1. Настраиваем порог срабатывания]
        try:
            threshold = CONFIDENCE_MAP.get(settings.ZAP_MIN_CONFIDENCE, "1")
            await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/ascan/action/setOptionAlertThreshold/",
                {"apikey": settings.ZAP_API_KEY, "String": threshold}
            )
            logger.info(f"ZAP Alert Threshold set to {settings.ZAP_MIN_CONFIDENCE} ({threshold})")
        except Exception as e:
            logger.warning(f"Failed to set ZAP Alert Threshold: {e}")

        # [SECURITY FIRST: 2. Жесткий контроль Scope для Паука]
        # Устанавливаем maxDepth = 0, чтобы сканер не уходил с указанного URL
        try:
            spider_depth = getattr(settings, "ZAP_SPIDER_MAX_DEPTH", "0")
            await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/spider/action/setOptionMaxDepth/",
                {"apikey": settings.ZAP_API_KEY, "Integer": spider_depth}
            )
            logger.info(f"ZAP Spider Max Depth set to {spider_depth}")
        except Exception as e:
            logger.warning(f"Failed to set Spider Max Depth: {e}")

        # [SECURITY FIRST: 3. Таймаут на правила для предотвращения зависаний (Path Traversal и т.д.)]
        try:
            max_rule_duration = getattr(settings, "ZAP_MAX_RULE_DURATION_MINS", "1")
            await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/ascan/action/setOptionMaxRuleDurationInMins/",
                {"apikey": settings.ZAP_API_KEY, "Integer": max_rule_duration}
            )
            logger.info(f"ZAP Active Scan Max Rule Duration set to {max_rule_duration} mins")
        except Exception as e:
            logger.warning(f"Failed to set AScan Max Rule Duration: {e}")

        # Fast mode: ограничиваем точки инъекции только URL и формами
        try:
            await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/ascan/action/setOptionTargetParamsInjectable/",
                {"apikey": settings.ZAP_API_KEY, "Integer": "31"},
            )
            logger.info("ZAP TargetParamsInjectable set to 31 (URL + forms only)")
        except Exception as e:
            logger.warning(f"Failed to set TargetParamsInjectable: {e}")

        # Отключаем самые медленные и тяжёлые правила активного сканера
        try:
            await disable_slow_scanners(client)
        except Exception as e:
            logger.warning(f"Failed to disable slow scanners: {e}")

        # Spider the target to discover forms and parameters
        try:
            spider_resp = await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/spider/action/scan/",
                {
                    "apikey": settings.ZAP_API_KEY,
                    "url": target,
                    "recurse": "false",  # не уходим рекурсивно за пределы заданного URL
                    "subtreeOnly": "true",  # остаёмся в пределах поддерева цели
                },
            )
            spider_id = spider_resp.get("scan")
            logger.info(f"Spider started for {target} with id={spider_id}")

            for _ in range(120):
                status_resp = await _zap_get(
                    client,
                    f"{settings.ZAP_API_URL}/JSON/spider/view/status/",
                    {"apikey": settings.ZAP_API_KEY, "scanId": spider_id},
                )
                if int(status_resp.get("status", 0)) >= 100:
                    break
                await asyncio.sleep(2)

            logger.info(f"Spider completed for {target}")
        except Exception as e:
            logger.warning(f"Spider failed for {target}: {e}")

        # Запускаем активный скан с отключенной рекурсией
        data = await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/ascan/action/scan/",
            {
                "apikey": settings.ZAP_API_KEY,
                "url": target,
                "recurse": "false",  # КРИТИЧНО для кибербезопасности: атаковать только указанный endpoint
                "inScopeOnly": "true",  # атаки только по URL-ам, попавшим в Scope ZAP
            }
        )

    scan_data = Scan(
        target=target,
        created_at=datetime.utcnow(),
        zap_index=int(data.get("scan")),
        user_id=user_id,
    )
    created_scan = await database_service.create(scan_data)
    logger.info(f"Started scan for target {target} with scan_id={created_scan.scan_id}")

    return {
        "scan_id": created_scan.scan_id,
        "scan_index": data.get("scan"),
        "zap_index": str(created_scan.zap_index),
    }

async def get_scan_status(scan_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/ascan/view/status/",
            {"apikey": settings.ZAP_API_KEY, "scanId": scan_id}
        )


async def get_alerts() -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
            {"apikey": settings.ZAP_API_KEY}
        )


async def get_alerts_with_evidence(baseurl: str = None) -> dict:
    params = {"apikey": settings.ZAP_API_KEY}
    if baseurl:
        params["baseurl"] = baseurl

    async with httpx.AsyncClient(timeout=60.0) as client:
        data = await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
            params
        )
        alerts = data.get("alerts", [])

        seen = set()
        unique_alerts = []

        for a in alerts:
            key = (a.get("alert"), a.get("url"), a.get("param"))
            if key not in seen:
                seen.add(key)
                unique_alerts.append({
                    "alert": a.get("alert"),
                    "risk": a.get("risk"),
                    "confidence": a.get("confidence"),
                    "url": a.get("url"),
                    "param": a.get("param"),
                    "evidence": a.get("evidence"),
                    "solution": a.get("solution"),
                    "reference": a.get("reference"),
                    "tags": a.get("tags"),
                    "cweid": a.get("cweid"),
                })
        
        # Filter by minimum confidence level
        min_conf = settings.ZAP_MIN_CONFIDENCE
        confidence_threshold = int(CONFIDENCE_MAP.get(min_conf, "1"))
        
        filtered = []
        for a in unique_alerts:
            if not a.get("evidence"):
                continue
            
            # ZAP confidence labels to numeric for comparison
            conf_label = a.get("confidence", "Low")
            conf_val = int(CONFIDENCE_MAP.get(conf_label, "0"))
            
            if conf_val >= confidence_threshold:
                filtered.append(a)

        return {"count": len(filtered), "alerts": filtered}


async def get_alerts_summary() -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alertsSummary/",
            {"apikey": settings.ZAP_API_KEY}
        )


async def get_alert_by_id(alert_id: str) -> dict:
    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _zap_get(
            client,
            f"{settings.ZAP_API_URL}/JSON/core/view/alert/",
            {"apikey": settings.ZAP_API_KEY, "id": alert_id}
        )


async def abort_scan(scan_id: str) -> dict:
    from core.database import async_session

    async with async_session() as db:
        database_service = AsyncDatabaseService(lambda: db)
        scan = await database_service.get(Scan, scan_id=scan_id)
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")

        zap_index = str(scan.zap_index)

    _cancelled_scans.add(str(scan_id))

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/ascan/action/stop/",
                {"apikey": settings.ZAP_API_KEY, "scanId": zap_index},
            )
        except Exception as e:
            logger.warning(f"ZAP active scan stop failed for {scan_id}: {e}")

        try:
            await _zap_get(
                client,
                f"{settings.ZAP_API_URL}/JSON/spider/action/stop/",
                {"apikey": settings.ZAP_API_KEY, "scanId": zap_index},
            )
        except Exception:
            pass

    async with async_session() as db:
        database_service = AsyncDatabaseService(lambda: db)
        await database_service.update(
            Scan, {"scan_id": scan_id}, {"status": "stopped"}
        )

    await manager.broadcast(str(scan_id), {
        "type": "stopped",
        "message": "Scan was stopped by user",
    })
    logger.info(f"Scan {scan_id} stopped by user")
    return {"status": "stopped", "scan_id": str(scan_id)}


async def run_scan(scan_id: int, target_url: str, scan_index: str):
    from core.database import async_session
    async with async_session() as db:
        await _run_scan_internal(scan_id, target_url, scan_index, db)


async def disable_slow_scanners(client: httpx.AsyncClient) -> None:
    """
    Disable the heaviest and slowest active scan rules to keep Fast Mode lightweight.

    Focus the scan on quick XSS and basic SQLi checks by disabling:
    - Time-based and blind SQL injection variants
    - Directory/path traversal and directory brute-force style checks
    - Legacy default-file checks for old stacks (IIS/SAP/etc.)
    - Heavy filesystem/metadata discovery scanners
    """
    # Time-based / blind SQLi and other heavy injection rules
    time_based_sql_and_heavy_ids = [
        "40019",  # SQL Injection MySQL (Time Based)
        "40020",  # SQL Injection Hypersonic (Time Based)
        "40021",  # SQL Injection Oracle (Time Based)
        "40022",  # SQL Injection Postgresql (Time Based)
        "40024",  # SQL Injection SQLite (Time Based)
        "40027",  # SQL Injection MsSQL (Time Based)
        "90037",  # Command Injection (Time Based)
        "90039",  # NoSQL Injection MongoDB (Time Based)
    ]

    # Directory brute force, path traversal and hidden file scanners
    directory_and_traversal_ids = [
        "0",      # Directory browsing
        "33",     # Directory Browsing
        "6",      # Directory/Path traversal
        "40035",  # Hidden File Scanner
        "90034",  # Cloud Metadata Attack
    ]

    # Legacy / default file checks for old platforms (IIS, SAP, WebSphere, etc.)
    legacy_platform_ids = [
        "20000",  # Cold Fusion default file
        "20001",  # Lotus Domino default files
        "20002",  # IIS default file
        "20003",  # Macromedia JRun default files
        "20004",  # Tomcat source file disclosure
        "20005",  # BEA WebLogic example files
        "20006",  # IBM WebSphere default files
    ]

    slow_ids = time_based_sql_and_heavy_ids + directory_and_traversal_ids + legacy_platform_ids
    ids_param = ",".join(slow_ids)

    if not ids_param:
        logger.info("No slow scanners configured to be disabled.")
        return

    await _zap_get(
        client,
        f"{settings.ZAP_API_URL}/JSON/ascan/action/disableScanners/",
        {
            "apikey": settings.ZAP_API_KEY,
            "ids": ids_param,
        },
    )
    logger.info(f"Disabled slow ZAP scanners (Fast Mode): {ids_param}")


async def _run_scan_internal(scan_id: int, target_url: str, scan_index: str, db: AsyncSession):
    database_service = AsyncDatabaseService(lambda: db)
    logger.info(f"Starting run_scan for scan_id={scan_id}, target={target_url}, zap_scan_index={scan_index}")
    try:
        seen_alert_ids = set()
        async with httpx.AsyncClient(timeout=60.0) as client:
            cancelled = False
            # Ожидаем завершения сканирования, без жёсткого таймаута, но с учётом Kill Switch
            while True:
                scan_id_str = str(scan_id)
                if scan_id_str in _cancelled_scans:
                    _cancelled_scans.discard(scan_id_str)
                    cancelled = True
                    logger.info(f"Scan {scan_id} cancelled by user during polling")
                    break

                status = await _zap_get(
                    client,
                    f"{settings.ZAP_API_URL}/JSON/ascan/view/status/",
                    {"apikey": settings.ZAP_API_KEY, "scanId": scan_index},
                )
                progress = int(status.get("status", 0))

                alerts_ids_resp = await _zap_get(
                    client,
                    f"{settings.ZAP_API_URL}/JSON/ascan/view/alertsIds/",
                    {"apikey": settings.ZAP_API_KEY, "scanId": scan_index},
                )
                current_alert_ids = alerts_ids_resp.get("alertsIds", [])

                new_alerts = []
                if isinstance(current_alert_ids, list):
                    for aid in current_alert_ids:
                        aid_str = str(aid)
                        if aid_str not in seen_alert_ids:
                            alert_detail_resp = await _zap_get(
                                client,
                                f"{settings.ZAP_API_URL}/JSON/core/view/alert/",
                                {"apikey": settings.ZAP_API_KEY, "id": aid_str},
                            )
                            alert_detail = alert_detail_resp.get("alert", {})
                            if alert_detail:
                                logger.debug(
                                    f"Scan {scan_id} found new alert: {alert_detail.get('alert')} on {alert_detail.get('url')}"
                                )
                                new_alerts.append(
                                    {
                                        "id": aid_str,
                                        "name": alert_detail.get("alert", "Unknown"),
                                        "risk": alert_detail.get("risk", "Info"),
                                        "url": alert_detail.get("url", ""),
                                    }
                                )
                            seen_alert_ids.add(aid_str)

                await manager.broadcast(
                    str(scan_id),
                    {
                        "type": "progress",
                        "progress": progress,
                        "new_alerts": new_alerts,
                        "total_alerts": len(seen_alert_ids),
                    },
                )

                if progress >= 100:
                    logger.info(f"ZAP scan {scan_id} reached 100% progress")
                    break

                await asyncio.sleep(5)

            if cancelled:
                return

            resp = await client.get(
                f"{settings.ZAP_API_URL}/JSON/core/view/alerts/",
                params={"apikey": settings.ZAP_API_KEY, "baseurl": target_url}
            )
            data = resp.json()
            vulnerabilities_raw = data.get("alerts", [])
            
            # Filter by minimum confidence level
            min_conf = settings.ZAP_MIN_CONFIDENCE
            confidence_threshold = int(CONFIDENCE_MAP.get(min_conf, "1"))
            
            filtered_vulnerabilities = []
            for v in vulnerabilities_raw:
                conf_label = v.get("confidence", "Low")
                conf_val = int(CONFIDENCE_MAP.get(conf_label, "0"))
                if conf_val >= confidence_threshold:
                    filtered_vulnerabilities.append(v)
            
            vulnerabilities_raw = filtered_vulnerabilities
            alerts_data = []

            for vuln_raw in vulnerabilities_raw:
                try:
                    message_id = vuln_raw.get("messageId")
                    parameter = vuln_raw.get("param")
                    payload = vuln_raw.get("attack")

                    request_text = ""
                    response_text = ""

                    if message_id:
                        try:
                            msg_resp = await client.get(
                                f"{settings.ZAP_API_URL}/JSON/core/view/message/",
                                params={"apikey": settings.ZAP_API_KEY, "id": message_id}
                            )
                            msg_data = msg_resp.json().get("message", {})
                            request_text = msg_data.get("requestHeader", "") + "\n\n" + msg_data.get("requestBody", "")
                            response_text = msg_data.get("responseHeader", "") + "\n\n" + msg_data.get("responseBody", "")
                        except Exception as e:
                            logger.error(f"Failed to fetch ZAP message ID {message_id}: {e}")

                    vuln = VulnerabilitySchema(**vuln_raw)
                    vuln_data = vuln.model_dump()
                    vuln_data["url"] = str(vuln_data["url"])
                    vuln_data["parameter"] = parameter
                    vuln_data["payload"] = payload
                    vuln_data["request"] = request_text
                    vuln_data["response"] = response_text

                    await database_service.create(Vulnerability(**vuln_data, scan_id=scan_id))
                    alerts_data.append(vuln_data)
                except Exception as ex:
                    logger.error(f"Error processing vulnerability row: {ex}", exc_info=True)

            await database_service.update(
                Scan,
                {"scan_id": scan_id},
                {"status": "done"}
            )
            
            await manager.broadcast(str(scan_id), {
                "type": "done",
                "progress": 100,
                "alerts_count": len(alerts_data),
                "total_alerts": len(seen_alert_ids),
                "alerts": alerts_data
            })
            logger.info(f"Scan {scan_id} completed successfully. Found {len(alerts_data)} vulnerabilities.")

    except Exception as e:
        await database_service.update(
            Scan,
            {"scan_id": scan_id},
            {"status": "error"}
        )
        await manager.broadcast(str(scan_id), {
            "type": "error",
            "message": str(e)
        })
        logger.error(f"Error in run_scan for scan_id={scan_id}: {e}", exc_info=True)
