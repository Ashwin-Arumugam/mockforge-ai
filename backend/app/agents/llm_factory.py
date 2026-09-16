import os
import json
import httpx
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel

class LLMProviderFactory:
    """
    Bring Your Own Key (BYOK) & Model Factory.
    Supports Ollama (Local/Free), Gemini, Groq, and OpenAI via OpenAI-compatible REST API interface.
    """
    def __init__(
        self, 
        provider: str = "auto",            # "ollama", "gemini", "groq", "openai", "auto"
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        self.provider = provider.lower()
        self.api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("GEMINI_API_KEY", "")
        self.base_url, self.model_name = self._resolve_endpoint_and_model(base_url, model_name)

    def _resolve_endpoint_and_model(self, base_url: Optional[str], model_name: Optional[str]):
        if self.provider == "ollama":
            url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            model = model_name or "llama3"
            return url, model
        elif self.provider == "groq":
            url = "https://api.groq.com/openai/v1"
            model = model_name or "llama-3.3-70b-versatile"
            return url, model
        elif self.provider == "gemini":
            url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            model = model_name or "gemini-2.0-flash"
            return url, model
        elif self.provider == "openai":
            url = "https://api.openai.com/v1"
            model = model_name or "gpt-4o-mini"
            return url, model
        else:
            # Auto-detect based on env vars
            if os.getenv("GROQ_API_KEY"):
                return "https://api.groq.com/openai/v1", model_name or "llama-3.3-70b-versatile"
            elif os.getenv("GEMINI_API_KEY"):
                return "https://generativelanguage.googleapis.com/v1beta/openai/", model_name or "gemini-2.0-flash"
            elif os.getenv("OPENAI_API_KEY"):
                return "https://api.openai.com/v1", model_name or "gpt-4o-mini"
            else:
                # Default to local Ollama fallback
                return "http://localhost:11434/v1", model_name or "llama3"

    def generate_structured_output(self, prompt: str, schema_class: Type[BaseModel]) -> Optional[Dict[str, Any]]:
        """
        Sends prompt to configured LLM provider requesting structured JSON output matching schema_class.
        Falls back gracefully if provider is unreachable or key is missing.
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        json_schema_prompt = f"{prompt}\n\nIMPORTANT: Respond ONLY with valid raw JSON matching this format:\n{schema_class.model_json_schema()}"

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a specialized software architecture AI agent."},
                {"role": "user", "content": json_schema_prompt}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"}
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(f"{self.base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"]
                    return json.loads(content)
        except Exception:
            pass # Fall back gracefully if LLM provider offline or key missing

        return None
