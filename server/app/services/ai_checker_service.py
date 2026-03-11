import json
import logging
from typing import Optional
from pydantic import BaseModel

from services.llm_service import LLMService

logger = logging.getLogger(__name__)

class AICheckerResult(BaseModel):
    id: str # To map back to the original finding
    is_false_positive: bool
    confidence_score: int
    severity_adjustment: str
    reasoning: str

class AICheckerService:
    def __init__(self):
        self.llm_service = LLMService()

    async def verify_vulnerabilities_batch(
        self,
        findings: list[dict]
    ) -> list[AICheckerResult]:
        """
        Processes a batch of findings to minimize LLM requests.
        findings: list of dicts with {id, vuln_type, url, parameter, payload, request_text, response_text}
        """
        if not findings:
            return []

        findings_formatted = []
        for f in findings:
            entry = f"""
            --- FINDING ID: {f['id']} ---
            - Type: {f['vuln_type']}
            - URL: {f['url']}
            - Parameter: {f.get('parameter', 'N/A')}
            - Payload: {f.get('payload', 'N/A')}
            - Request Header/Body (Sample): {f.get('request_text', 'N/A')[:500]}
            - Response Header/Body (Sample): {f.get('response_text', 'N/A')[:1000]}
            """
            findings_formatted.append(entry)

        prompt = f"""
        You are an expert Application Security Analyst. Analyze the following batch of {len(findings)} automated scanner findings.
        Determine if each is a False Positive or True Positive.

        {"".join(findings_formatted)}

        Return a JSON list of objects, one for each FINDING ID, matching this schema:
        {{
            "id": "original finding id",
            "is_false_positive": boolean,
            "confidence_score": integer (0-100),
            "severity_adjustment": "Informational"|"Low"|"Medium"|"High"|"Critical",
            "reasoning": "string"
        }}
        Output ONLY the JSON list.
        """

        try:
            llm_response = await self.llm_service.call_llm(prompt)
            text_response = llm_response.get("response", "")
            
            start = text_response.find('[')
            end = text_response.rfind(']') + 1
            if start != -1 and end != -1:
                json_str = text_response[start:end]
                data = json.loads(json_str)
                return [AICheckerResult(**item) for item in data]
            
            logger.warning(f"Could not parse valid JSON array from LLM: {text_response}")
            return []
        except Exception as e:
            logger.error(f"Batch AI Checker error: {e}", exc_info=True)
            return []

    async def verify_vulnerability(
        self,
        vuln_type: str,
        url: str,
        parameter: Optional[str] = None,
        payload: Optional[str] = None,
        request_text: Optional[str] = None,
        response_text: Optional[str] = None
    ) -> AICheckerResult:
        # Re-using the batch logic for a single vulnerability for consistency
        results = await self.verify_vulnerabilities_batch([{
            "id": "single",
            "vuln_type": vuln_type,
            "url": url,
            "parameter": parameter,
            "payload": payload,
            "request_text": request_text,
            "response_text": response_text
        }])
        if results:
            return results[0]
        
        return AICheckerResult(
            id="single",
            is_false_positive=False,
            confidence_score=0,
            severity_adjustment="Unknown",
            reasoning="AI analysis failed or returned invalid format."
        )
