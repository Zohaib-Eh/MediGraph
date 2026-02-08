"""
Shared LLM factory: create chat model from LLM_PROVIDER and env.
Default: Ollama (local). Also supports Gemini, OpenAI, Anthropic.
"""

import logging
import os
from typing import Optional, Any

logger = logging.getLogger(__name__)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.0,
) -> Optional[Any]:
    """
    Create a LangChain chat model from env and optional overrides.

    Env: LLM_PROVIDER (ollama | gemini | openai | anthropic), OLLAMA_MODEL, OLLAMA_BASE_URL, etc.

    Returns:
        Chat model instance or None if provider unavailable / missing API key.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "ollama")).lower().strip()

    if provider == "ollama":
        return _get_ollama(model, temperature)

    if provider == "gemini":
        if GEMINI_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                model_name = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
                try:
                    return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=api_key)
                except Exception as e:
                    logger.warning("Gemini init failed (%s), falling back to Ollama.", e)
            else:
                logger.warning("GOOGLE_API_KEY not set. Falling back to Ollama.")
        else:
            logger.warning("langchain-google-genai not installed. Falling back to Ollama.")
        return _get_ollama(model, temperature)

    if provider == "openai":
        if not OPENAI_AVAILABLE:
            logger.warning("langchain-openai not installed. pip install langchain-openai")
            return None
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. Set it in backend/.env or environment (required when LLM_PROVIDER=openai).")
            return None
        model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return ChatOpenAI(model=model_name, temperature=temperature, api_key=api_key)

    if provider == "anthropic":
        if not ANTHROPIC_AVAILABLE:
            logger.warning("langchain-anthropic not installed. pip install langchain-anthropic")
            return None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Set it in backend/.env or environment (required when LLM_PROVIDER=anthropic).")
            return None
        model_name = model or os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        return ChatAnthropic(model=model_name, temperature=temperature, api_key=api_key)

    return None


def _get_ollama(model: Optional[str], temperature: float) -> Optional[Any]:
    """Build ChatOllama. Uses OLLAMA_MODEL and optionally OLLAMA_BASE_URL (e.g. for Docker: http://host.docker.internal:11434)."""
    if not OLLAMA_AVAILABLE:
        logger.warning("langchain-ollama not installed. pip install langchain-ollama")
        return None
    model_name = model or os.getenv("OLLAMA_MODEL", "llama3.2")
    base_url = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST")
    try:
        kwargs = {"model": model_name, "temperature": temperature}
        if base_url:
            kwargs["base_url"] = base_url.rstrip("/")
        return ChatOllama(**kwargs)
    except Exception as e:
        logger.warning("Ollama not available: %s", e)
        return None
