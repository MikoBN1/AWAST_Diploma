import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import re

LLM_URL= os.getenv("LLM_URL")
MODEL = os.getenv("MODEL")
class LLMService:
    def __init__(self, llm_url: str = LLM_URL, model: str = MODEL):
        self.client = httpx.AsyncClient(verify=False, timeout=None)
        self.url = llm_url
        self.model = model

    # async def call_llm(self, prompt: str):
    #     body = self.create_request_body(prompt)
    #
    #     resp = await self.client.post(self.url, json=body)
    #     resp.raise_for_status()
    #
    #     return resp.json()

    @staticmethod
    async def call_llm(prompt: str):
        await asyncio.sleep(3)
        return {"text":"content: {<script>alert(1)</script>} {<img src=x onerror=alert(1)>} {javascript:alert(1)}"}

    def create_request_body(self, prompt: str):
        return {
            "prompt": prompt,
            "temperature": 0,
            "model": self.model,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "num_thread": 4,
                "num_predict": 100,
            }
        }

    @staticmethod
    def extract_payloads_from_text(text: str):
        items = re.findall(r"\{(.*?)}", text)
        return items

    async def ask_for_payloads(self, target:str, vuln_type:str, params:str):
        prompt = f"For this target: {target} with params {params} and vuln type {vuln_type}, generate 3 payloads."
        llm_response = await self.call_llm(prompt)
        payloads = self.extract_payloads_from_text(llm_response["text"])
        return payloads

