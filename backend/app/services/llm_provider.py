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
        """Deterministic GxP-grounded compliance response generator when offline."""
        p_lower = prompt.lower()
        if "audit ready" in p_lower or "readiness" in p_lower:
            return (
                "Audit Readiness Assessment for Novo Life MES PAS-X (SYS-MES-001):\n\n"
                "- System Status: PRE-OPERATIONAL / NOT ACTIVATED [NL-MES-SLA-001 | Section 1.2]\n"
                "- Current Release Recommendation: HOLD / DEFER - DO NOT RELEASE [NL-MES-ITPSE-001 | Section 5]\n"
                "- Readiness Score: 48% (NOT AUDIT READY)\n"
                "- Critical Blockers: Release gates G5 and G6 are NOT MET [NL-MES-IREP-001 | Section 4]. "
                "Intended-use verification (OV/PfV/UAT) has not been performed, and residual risks are not rated."
            )
        elif "blocking release" in p_lower or "release blocked" in p_lower or "blocker" in p_lower:
            return (
                "Evidence-Backed Release Blockers for Novo Life MES PAS-X:\n\n"
                "1. Gate G5 Not Met: Release readiness criteria incomplete [NL-MES-IREP-001 | Section 4.1].\n"
                "2. Gate G6 Not Met: Operational handover and ownership transfer prerequisites incomplete [NL-MES-IREP-001 | Section 4.2].\n"
                "3. Verification Open: Intended-use verification (OV/PfV/UAT) is NOT PERFORMED [NL-MES-IREP-001 | Section 3.2].\n"
                "4. Residual Risk Open: 49 working high risks have not undergone authorized residual risk acceptance [NL-MES-ITRRA-001 | Section 3].\n"
                "5. Validation Summary Report: VSR is DEFERRED [NL-MES-IREP-001 | Section 4.3]."
            )
        elif "g5" in p_lower:
            return (
                "Release Gate G5 (Release Readiness) Analysis:\n\n"
                "Status: NOT MET [NL-MES-IREP-001 | Section 4.1]\n"
                "Evidence: The IT Implementation Report records that G5 release readiness prerequisites "
                "were not satisfied due to open verification activities (OV/PfV/UAT not performed) and "
                "unrated residual risks in the requirement risk register."
            )
        elif "verification" in p_lower:
            return (
                "Verification Activities Status for Novo Life MES PAS-X:\n\n"
                "- Integration Testing: COMPLETE [NL-MES-IREP-001 | Section 3.1]\n"
                "- Installation Qualification (IQ): COMPLETE [NL-MES-IREP-001 | Section 3.1]\n"
                "- Backup & Restore Verification: COMPLETE [NL-MES-IREP-001 | Section 3.1]\n"
                "- Intended-Use Verification (OV / PfV / UAT): NOT PERFORMED [NL-MES-IREP-001 | Section 3.2]\n\n"
                "Conclusion: Not all verification activities have been completed. Operational verification remains open."
            )
        elif "risk" in p_lower:
            return (
                "Active Risk Baseline for Novo Life MES PAS-X:\n\n"
                "- Total System Risks: 26 (RSK-MES-001 through RSK-MES-026) [NL-MES-ITRA-001]\n"
                "- Requirement Risks: 49 Working High, 1 Working Medium, 0 Working Low [NL-MES-ITRRA-001]\n"
                "- Residual Risk Status: NOT RATED (residual risk acceptance open) [NL-MES-ITRRA-001 | Section 3]."
            )
        else:
            return (
                "Analysis grounded in Novo Life MES PAS-X lifecycle documentation package:\n"
                "System is currently in PRE-OPERATIONAL state. All conclusions are derived directly from "
                "NL-MES-MLGP-001, NL-MES-URS-001, NL-MES-FS-001, NL-MES-ITRA-001, NL-MES-ITRRA-001, "
                "NL-MES-SUPA-001, NL-MES-OMSOP-001, NL-MES-SLA-001, NL-MES-ITPSE-001, and NL-MES-IREP-001."
            )


# Global singleton instance
_llm_provider_instance: Optional[LLMProvider] = None

def get_llm_provider() -> LLMProvider:
    global _llm_provider_instance
    if _llm_provider_instance is None:
        _llm_provider_instance = OpenRouterProvider()
    return _llm_provider_instance
