import os
from dotenv import load_dotenv
import httpx
import re

load_dotenv()
LLM_URL= os.getenv("LLM_URL")
MODEL = os.getenv("MODEL")
class LLMService:
    def __init__(self, llm_url: str = LLM_URL, model: str = MODEL):
        self.client = httpx.AsyncClient(verify=False, timeout=None)
        self.url = llm_url
        self.model = model

    async def call_llm(self, prompt: str):
        body = self.create_request_body(prompt)

        resp = await self.client.post(self.url, json=body)
        resp.raise_for_status()

        return resp.json()

    # @staticmethod
    # async def call_llm(prompt: str):
    #     await asyncio.sleep(3)
    #     return {"text":"content: {<script>alert(1)</script>} {<img src=x onerror=alert(1)>} {javascript:alert(1)}"}

    def create_request_body(self, prompt: str):
        return {
            "prompt": prompt,
            "temperature": 0,
            "model": self.model,
            "stream": False,
            "options": {
                "num_ctx": 8192,
                "num_thread": 4,
            }
        }

    @staticmethod
    def extract_payloads_from_text(text: str):
        # Primary parsing: look for `{payload}`
        items = re.findall(r"\{(.*?)}", text)
        
        # Fallback parsing: if the LLM forgot {} but used formatting like 1. payload, 2. payload, or just lines
        if not items:
            # Try splitting by lines and taking non-empty lines that look like code/payloads
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            for line in lines:
                # Remove markdown code formatting, list numbers, or bullets
                clean_line = re.sub(r'^(?:\d+\.|\-|\*|`+)\s*', '', line).strip('`')
                if clean_line:
                    items.append(clean_line)
                    
        # Use dict.fromkeys to remove duplicates while preserving insertion order
        return list(dict.fromkeys(items))

    async def ask_for_payloads(self, target:str, vuln_type:str, params:str, previous_payloads: list = None):
        previous_text = ""
        if previous_payloads:
            previous_text = f"PREVIOUSLY ATTEMPTED PAYLOADS (DO NOT USE THESE AGAIN):\n" + "\n".join([f"- {p}" for p in previous_payloads])

        prompt = f"""
        You are an advanced Penetration Testing Assistant. Your task is to provide exactly 5 payloads for an automated scanner.
        Target URL: {target}
        Parameter to inject: {params}
        Vulnerability Type: {vuln_type}
        
        {previous_text}
        
        CRITICAL FORMATTING RULES (DO NOT FAIL):
        1. YOU MUST STRICTLY WRAP EVERY PAYLOAD IN CURLY BRACES: {{payload}}.
        2. DO NOT output numbered lists like "1. payload". DO NOT output introductory text.
        3. Valid output format: {{payload1}} {{payload2}} {{payload3}} {{payload4}} {{payload5}}
        
        CRITICAL EXPLOITATION RULES:
        1. EVERY payload must be thoroughly unique and use a different evasion strategy.
        2. DO NOT submit minor variations (e.g. alert(1) vs alert(2)).
        3. IN HTML CONTEXTS ALWAYS wrap HTML attributes in double quotes (e.g., <img src="x" onerror="alert(1)"/>)
        
        TECHNIQUES TO USE (Choose 5 DIFFERENT ones for the vulnerability):
        - Standard Base Vectors (e.g. <script>, <svg>, <iframe>, <object>)
        - Context Breakout (e.g. " autofocus onfocus="..., " onerror="..., '>-)
        - Scheme Based (e.g. javascript:, data:, vbscript:)
        - Encoding/Obfuscation bypass (e.g. URL Encoding, HTML Entities, Hex encoding, eval(atob()))
        - WAF Evasion (e.g. Mixed case tags <sCrIpT>, Null bytes, whitespace manipulation, template injections)
        - Polyglots
        
        CRITICAL: For XSS, you MUST provide exactly one payload from each of these 5 categories. DO NOT REPEAT a category (e.g., do not provide two <script> tags, or two onerror= events):
        1. A `<script>` tag execution.
        2. An HTML tag event handler (e.g., `<svg onload=...>`, `<img onerror=...>`, `<body onload=...>`, autofocus).
        3. A Javascript URI scheme (`javascript:alert(1)`).
        4. An execution via an exotic tag/attribute (e.g., `<iframe>`, `<object>`, `<embed>`).
        5. A WAF evasion technique (e.g., mixed case, encoded, or obfuscated like `eval(atob(...))`).
        
        Example Output for XSS:
        {{<script>alert(1)</script>}} {{\" autofocus onfocus=\"alert(1)\"}} {{<svg/onload=\"alert(1)\">}} {{javascript:alert(1)}} {{"/><script>eval(atob("YWxlcnQoMSk="));</script>}}
        """
        llm_response = await self.call_llm(prompt)
        payloads = self.extract_payloads_from_text(llm_response["response"])
        return payloads


    async def analyze_logical_vulns(self, context_chunk: str):
        prompt = f"""
        You are a Senior AppSec Engineer. Analyze the provided OpenAPI definition.

        RULES:
        1. STRICTLY adhere to the provided context. Do NOT invent paths that are not in the "paths" section.
        2. If a description mentions "SQL", "Database", or "Filter", consider SQL Injection first.
        3. For DELETE requests, do not check for Mass Assignment (as they rarely have bodies).
        4. Focus on logical flows: check if sensitive endpoints (like /admin) lack the "security" key.

        SWAGGER CHUNK:
        {context_chunk}
        
        Identify potential logical vulnerabilities. Focus on:
        1. IDOR (Insecure Direct Object References) - e.g., endpoints taking IDs without clear authorization checks.
        2. Mass Assignment - e.g., endpoints accepting too many fields.
        3. Broken Access Control - e.g., sensitive admin endpoints that might lack protection.
        4. Business Logic Errors.

        Output the result ONLY as a JSON list of objects with the following keys:
        - "title": Short title of the vulnerability
        - "description": Detailed explanation of why this is a potential vulnerability
        - "severity": "High", "Medium", or "Low"
        - "location": The specific endpoint or path involved
        - "remediation": Suggested fix

        If no vulnerabilities are found, return an empty list: []
        """
        # Note: In a real scenario, we might want to enforce JSON output more strictly depending on the LLM capability.
        response = await self.call_llm(prompt)
        text_response = response["response"] # Handle Ollama structure
        print("response: ", text_response)
        # Try to clean up the response to get just the JSON part if there's extra text
        try:
             # Basic cleanup to find the first [ and last ]
            start = text_response.find('[')
            end = text_response.rfind(']') + 1
            if start != -1 and end != -1:
                return text_response[start:end]
            return "[]"
        except:
            return "[]"

    async def generate_context_aware_xss(self, context_html: str) -> str:
        prompt = f"""
        You are a penetration testing assistant. The input is reflected in the following HTML context:
        {context_html}
        Generate a single highly advanced XSS payload that breaks out of this specific context.
        Provide JUST the payload, no other text.
        """
        response = await self.call_llm(prompt)
        return response["response"].strip()

    async def generate_waf_bypass(self, vuln_type: str, blocked_payload: str) -> str:
        prompt = f"""
        You are a penetration testing assistant. The payload '{blocked_payload}' for '{vuln_type}' was blocked by a WAF.
        Generate 1 obfuscated variation of this payload using URL encoding, comments, or other bypass techniques.
        Provide JUST the payload, no other text.
        """
        response = await self.call_llm(prompt)
        return response["response"].strip()

    async def analyze_ssti_error(self, error_trace: str) -> str:
        prompt = f"""
        You are a penetration testing assistant. Based on this HTML error stack trace:
        {error_trace[:1000]}
        What template engine is the server using, and what is the payload to achieve Remote Code Execution?
        Provide JUST the payload, no other text.
        """
        response = await self.call_llm(prompt)
        return response["response"].strip()

    async def guess_api_parameters(self, json_structure: dict) -> dict:
        import json
        prompt = f"""
        You are a penetration testing assistant. Here is a JSON object for a target API: {json.dumps(json_structure)}.
        Predict hidden JSON properties that might grant admin privileges or access to other users (e.g., "role": "admin").
        Provide the answer as a ONLY ONE JSON object with those additional properties merged into the original, no other text.
        """
        response = await self.call_llm(prompt)
        text_response = response["response"]
        try:
            start = text_response.find('{')
            end = text_response.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(text_response[start:end])
            return json_structure
        except:
            return json_structure

    async def analyze_sql_error(self, error_response: str) -> str:
        prompt = f"""
        You are a penetration testing assistant. Here is a database error message:
        {error_response[:1000]}
        Based on this error, what is the exact SQL payload to exploit this vulnerability?
        Provide JUST the payload, no other text.
        """
        response = await self.call_llm(prompt)
        return response["response"].strip()

    async def generate_prompt_injection(self, target_response: str = "") -> str:
        prompt = f"""
        You are an AI red teamer. Generate a single highly advanced payload for Prompt Injection / AI Jailbreaking.
        """
        if target_response:
             prompt += f"\nThe previous attempt resulted in: {target_response[:500]}. Adapt the payload."
        prompt += "\nProvide JUST the payload, no other text."
        response = await self.call_llm(prompt)
        return response["response"].strip()
