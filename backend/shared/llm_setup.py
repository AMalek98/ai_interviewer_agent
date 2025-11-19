"""
LLM Setup and Initialization Module

This module provides centralized LLM configuration for all interview types.
It handles:
- Environment variable loading
- API key validation
- LLM initialization with appropriate parameters
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Optional


# Global LLM instance (lazy initialization)
_llm_instance: Optional[ChatGoogleGenerativeAI] = None


def load_env() -> None:
    """
    Load environment variables from config/.env file

    Raises:
        FileNotFoundError: If .env file is not found
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Environment file not found at: {env_path}")

    load_dotenv(env_path)
    print(f"✅ Environment loaded from: {env_path}")


def validate_api_key() -> str:
    """
    Validate that the GOOGLE_API_KEY is present in environment

    Returns:
        str: The API key

    Raises:
        ValueError: If API key is not found
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("=" * 60)
        print("❌ ERROR: GOOGLE_API_KEY not found!")
        print("Please check that backend/config/.env contains:")
        print("GOOGLE_API_KEY=your_api_key_here")
        print("=" * 60)
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    # Set in environment for langchain
    os.environ["GOOGLE_API_KEY"] = api_key
    return api_key


def get_llm(model: str = "gemini-2.0-flash", temperature: float = 0.3,
            max_tokens: Optional[int] = None, force_new: bool = False) -> ChatGoogleGenerativeAI:
    """
    Get or create the LLM instance

    Args:
        model: Model name to use (default: "gemini-2.0-flash")
        temperature: Temperature for generation (default: 0.3)
        max_tokens: Maximum tokens to generate (default: None)
        force_new: Force creation of new instance (default: False)

    Returns:
        ChatGoogleGenerativeAI: Initialized LLM instance

    Raises:
        ValueError: If API key validation fails
    """
    global _llm_instance

    # Return cached instance if available and not forcing new
    if _llm_instance is not None and not force_new:
        return _llm_instance

    # Validate API key
    validate_api_key()

    # Create LLM instance
    llm_kwargs = {
        "model": model,
        "temperature": temperature,
    }

    if max_tokens is not None:
        llm_kwargs["max_tokens"] = max_tokens

    _llm_instance = ChatGoogleGenerativeAI(**llm_kwargs)
    print(f"✅ LLM initialized: {model} (temp={temperature})")

    return _llm_instance


def initialize_llm(model: str = "gemini-2.0-flash", temperature: float = 0.3,
                   max_tokens: Optional[int] = None) -> ChatGoogleGenerativeAI:
    """
    Initialize LLM with environment loading (convenience function)

    This function handles the complete initialization process:
    1. Load environment variables
    2. Validate API key
    3. Create and return LLM instance

    Args:
        model: Model name to use (default: "gemini-2.0-flash")
        temperature: Temperature for generation (default: 0.3)
        max_tokens: Maximum tokens to generate (default: None)

    Returns:
        ChatGoogleGenerativeAI: Initialized LLM instance
    """
    load_env()
    return get_llm(model=model, temperature=temperature, max_tokens=max_tokens, force_new=True)


__all__ = ['load_env', 'validate_api_key', 'get_llm', 'initialize_llm']
