import yaml
import json
import logging
from typing import List, Dict, Any
from schemas.swagger_schema import VulnerabilityFinding
from services.llm_service import LLMService

class SwaggerService:
    def __init__(self):
        self.llm_service = LLMService()

    def parse_swagger(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        try:
            content_str = file_content.decode("utf-8")
            if filename.endswith(".json"):
                 return json.loads(content_str)
            elif filename.endswith(".yaml") or filename.endswith(".yml"):
                return yaml.safe_load(content_str)
            else:
                # Try JSON first then YAML as fallback
                try:
                    return json.loads(content_str)
                except json.JSONDecodeError:
                    return yaml.safe_load(content_str)
        except Exception as e:
            raise ValueError(f"Failed to parse Swagger file: {e}")

    def segment_swagger(self, swagger_dict: Dict[str, Any]) -> List[str]:
        """
        Segment the swagger definition into chunks where each chunk contains exactly one endpoint (path).
        """
        paths = swagger_dict.get("paths", {})
        chunks = []
        
        # Prepare the base chunk with everything except paths
        # This preserves info, components, definitions, securityDefinitions, etc.
        base_chunk = {k: v for k, v in swagger_dict.items() if k != "paths"}
        
        for path, methods in paths.items():
            # Create a shallow copy of the base chunk
            chunk = base_chunk.copy()
            # Set paths to contain ONLY the current path
            chunk["paths"] = {path: methods}
            chunks.append(json.dumps(chunk, indent=2))

        return chunks

    async def analyze_swagger(self, file_content: bytes, filename: str) -> List[VulnerabilityFinding]:
        swagger_dict = self.parse_swagger(file_content, filename)
        chunks = self.segment_swagger(swagger_dict)
        
        all_findings = []
        
        for chunk in chunks:
            try:
                # Send to LLM
                json_response_str = await self.llm_service.analyze_logical_vulns(chunk)
                findings_data = json.loads(json_response_str)
                
                for f in findings_data:
                    # Validate against schema roughly
                    if "title" in f and "description" in f:
                        all_findings.append(VulnerabilityFinding(**f))
            except Exception as e:
                logging.error(f"Error analyzing chunk: {e}")
                continue
                
        return all_findings
