import os
import time
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Type, Dict, Any, Iterator
from pydantic import BaseModel
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for all AI LLM providers in GxP compliance mesh."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text completion from prompt."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        """Generate strictly structured output validated against a Pydantic schema."""
        pass

    @abstractmethod
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Iterator[str]:
        """Stream completion tokens."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform non-blocking health check without exposing secret keys."""
        pass


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter-compatible LLM Provider.
    Adheres to OpenAI-compatible client interface with configurable model and endpoint.
    Includes deterministic fallback when API key is missing or endpoint is offline.
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key if api_key is not None else (settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY)
        self.base_url = base_url or settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1"
        self.model_name = model_name or settings.OPENROUTER_MODEL or settings.AI_MODEL or "anthropic/claude-3.5-sonnet"
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    default_headers={
                        "HTTP-Referer": "https://novonordisk.com",
                        "X-Title": "Novo Nordisk GxP Copilot"
                    },
                    timeout=12.0
                )
                logger.info(f"Initialized OpenRouterProvider with model: {self.model_name}")
            except Exception as e:
                logger.warning(f"Could not initialize OpenRouter client: {e}. Fallback active.")
                self.client = None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        temp = temperature if temperature is not None else settings.AI_TEMPERATURE
        max_t = max_tokens if max_tokens is not None else settings.AI_MAX_TOKENS
        
        if self.client and self.api_key:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temp,
                    max_tokens=max_t
                )
                return resp.choices[0].message.content or ""
            except Exception as err:
                logger.error(f"OpenRouter API call failed: {err}. Executing deterministic fallback.")
                
        # Deterministic grounded fallback for offline / mock hackathon operation
        return self._fallback_generate(prompt, system_prompt)

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        if self.client and self.api_key:
            try:
                # Request JSON output
                schema_json = json.dumps(response_model.model_json_schema())
                augmented_prompt = (
                    f"{prompt}\n\n"
                    f"Respond ONLY with a valid JSON object adhering strictly to this JSON Schema:\n"
                    f"{schema_json}\nDo not include backticks, markdown, or commentary."
                )
                raw = self.generate(augmented_prompt, system_prompt=system_prompt, temperature=0.0)
                raw_clean = raw.strip()
                if raw_clean.startswith("```json"):
                    raw_clean = raw_clean[7:]
                if raw_clean.startswith("```"):
                    raw_clean = raw_clean[3:]
                if raw_clean.endswith("```"):
                    raw_clean = raw_clean[:-3]
                raw_clean = raw_clean.strip()
                parsed = json.loads(raw_clean)
                return response_model.model_validate(parsed)
            except Exception as e:
                logger.warning(f"Structured OpenRouter output parsing failed: {e}. Generating default schema instance.")
        
        # Instantiate default instance if possible
        try:
            return response_model()
        except Exception:
            raise RuntimeError(f"Could not generate structured instance for {response_model.__name__}")

    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Iterator[str]:
        if self.client and self.api_key:
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                
                stream_resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=settings.AI_TEMPERATURE,
                    max_tokens=settings.AI_MAX_TOKENS,
                    stream=True
                )
                for chunk in stream_resp:
                    delta = chunk.choices[0].delta.content or ""
                    if delta:
                        yield delta
                return
            except Exception as e:
                logger.error(f"Streaming failed: {e}. Yielding fallback.")
        
        fallback_text = self._fallback_generate(prompt, system_prompt)
        yield fallback_text

    def health_check(self) -> Dict[str, Any]:
        start = time.time()
        has_key = bool(self.api_key)
        status = "Healthy" if has_key and self.client else "Offline Fallback"
        latency = 0.0
        
        if has_key and self.client:
            try:
                # Fast ping check
                _ = self.client.models.list()
                latency = round((time.time() - start) * 1000, 1)
                status = "Healthy"
            except Exception:
                status = "Degraded (Network unreachable, using fallback)"
                latency = round((time.time() - start) * 1000, 1)
        else:
            latency = 1.2
            
        return {
            "provider": "OpenRouter",
            "model": self.model_name,
            "status": status,
            "has_api_key": has_key,
            "base_url": self.base_url,
            "latency_ms": latency,
            "last_check": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    def _fallback_generate(self, prompt: str, system_prompt: Optional[str]) -> str:
        """Deterministic GxP-grounded compliance response generator when offline. Extractive only."""
        
        # Extract evidence chunks provided in the prompt
        evidence_snippets = []
        if "CONTEXT:" in prompt and "USER QUESTION:" in prompt:
            context_block = prompt.split("CONTEXT:")[1].split("USER QUESTION:")[0].strip()
            
            # Extract chunks based on "--- SOURCE:"
            if context_block:
                chunks = context_block.split("--- SOURCE:")
                for chunk in chunks:
                    if not chunk.strip():
                        continue
                    evidence_snippets.append(chunk.strip())
                    
        fallback_ans = "### OFFLINE EVIDENCE SUMMARY\n\nAssessment: UNKNOWN / NOT ASSESSED\n\n"
        fallback_ans += "The local model was unavailable. This is an extractive summary of the provided context.\n\n"
        
        fallback_ans += "#### Evidence\n"
        if not evidence_snippets:
            fallback_ans += "Unsupported / missing:\nNo evidence was found matching the query.\n\n"
        else:
            for snip in evidence_snippets:
                lines = snip.split("\n")
                if lines:
                    header = lines[0].replace("---", "").strip()
                    content = "\n".join(lines[1:]).strip()
                    if len(content) > 300:
                        content = content[:300] + "..."
                    fallback_ans += f"**[{header}]**\n> {content}\n\n"
        
        fallback_ans += "#### Findings\n"
        fallback_ans += "Extracted from source evidence only. No business inference made.\n\n"
        
        fallback_ans += "#### Release Gates\n"
        fallback_ans += "UNKNOWN / NOT ASSESSED (offline mode).\n\n"
        
        fallback_ans += "#### Uncertainty\n"
        fallback_ans += "HIGH. This is a deterministic offline fallback; AI synthesis was not performed.\n"
                    
        return fallback_ans.strip()


# Global singleton instance
_llm_provider_instance: Optional[LLMProvider] = None

def get_llm_provider() -> LLMProvider:
    global _llm_provider_instance
    if _llm_provider_instance is None:
        _llm_provider_instance = OpenRouterProvider()
    return _llm_provider_instance
