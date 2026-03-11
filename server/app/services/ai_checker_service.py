import json
import logging
from typing import Optional
from pydantic import BaseModel

from services.llm_service import LLMService

logger = logging.getLogger(__name__)

class AICheckerResult(BaseModel):
    is_false_positive: bool
    confidence_score: int
    severity_adjustment: str
    reasoning: str

class AICheckerService:
    def __init__(self):
        self.llm_service = LLMService()

    async def verify_vulnerability(
        self,
        vuln_type: str,
        url: str,
        parameter: Optional[str] = None,
        payload: Optional[str] = None,
        request_text: Optional[str] = None,
        response_text: Optional[str] = None
    ) -> AICheckerResult:
        prompt = f"""
        You are an expert Application Security Analyst. Your job is to review automated scanner results and determine if they are False Positives or True Positives based on the provided HTTP request, response, and payload.
        
        Analyze the following vulnerability report:
        - Vulnerability Type: {vuln_type}
        - Target URL: {url}
        - Parameter: {parameter or 'N/A'}
        - Payload Sent: {payload or 'N/A'}
        
        HTTP Request:
        {request_text[:2000] if request_text else 'N/A'}
        
        HTTP Response:
        {response_text[:2000] if response_text else 'N/A'}
        
        Evaluate whether the payload actually executed or had the intended impact in the response. For example, for XSS verify if the payload was reflected in a way that executes as Javascript.
        Explicitly determine if this is a False Positive.
        
        You MUST respond ONLY with a valid JSON object matching this schema:
        {{
          "is_false_positive": true or false,
          "confidence_score": integer between 0 and 100,
          "severity_adjustment": "Informational" or "Low" or "Medium" or "High" or "Critical",
          "reasoning": "Detailed string explaining why it is a false positive or true positive."
        }}
        Do NOT output anything else except the JSON. Do NOT wrap the JSON in markdown code blocks.
        """
        
        try:
            llm_response = await self.llm_service.call_llm(prompt)
            text_response = llm_response.get("response", "")
            
            # Extract JSON from the raw response text
            start = text_response.find('{')
            end = text_response.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = text_response[start:end]
                data = json.loads(json_str)
                return AICheckerResult(**data)
            
            logger.warning(f"Could not parse valid JSON from LLM: {text_response}")
            return AICheckerResult(
                is_false_positive=False,
                confidence_score=0,
                severity_adjustment="Unknown",
                reasoning=f"Failed to parse AI response. Raw response: {text_response[:200]}"
            )
        except Exception as e:
            logger.error(f"AI Checker error: {e}", exc_info=True)
            return AICheckerResult(
                is_false_positive=False,
                confidence_score=0,
                severity_adjustment="Unknown",
                reasoning=f"AI inference failed: {str(e)}"
            )
