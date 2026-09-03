import pytest
from backend.app.services.llm_provider import OpenRouterProvider, get_llm_provider
from backend.app.services.embedding_provider import get_embedding_provider

def test_openrouter_provider_initialization():
    provider = get_llm_provider()
    assert provider is not None
    assert isinstance(provider, OpenRouterProvider)

def test_openrouter_health_check_no_secret_exposure():
    provider = get_llm_provider()
    health = provider.health_check()
    assert "provider" in health
    assert health["provider"] == "OpenRouter"
    assert "model" in health
    assert "status" in health
    # Ensure sensitive API keys are never exposed
    assert "OPENROUTER_API_KEY" not in health
    assert "api_key" not in health
    assert "has_api_key" in health
    assert isinstance(health["has_api_key"], bool)

def test_deterministic_fallback_generation():
    provider = OpenRouterProvider(api_key="")
    ans = provider.generate("Is the MES PAS-X system audit ready?")
    assert "Audit Readiness Assessment" in ans
    assert "HOLD / DEFER" in ans or "PRE-OPERATIONAL" in ans

    blocker_ans = provider.generate("What is blocking release?")
    assert "Gate G5" in blocker_ans or "verification" in blocker_ans.lower()

def test_deterministic_embedding_provider():
    emb_provider = get_embedding_provider()
    vec = emb_provider.embed_text("User Requirement Specification URS-001")
    assert len(vec) == 384
    # Check that vector is normalized (L2 norm approx 1.0)
    import math
    norm = math.sqrt(sum(x*x for x in vec))
    assert abs(norm - 1.0) < 1e-4

    # Determinism check: identical string yields identical vector
    vec2 = emb_provider.embed_text("User Requirement Specification URS-001")
    assert vec == vec2
