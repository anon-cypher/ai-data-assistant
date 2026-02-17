from openai import OpenAI
from app.utils.config import LLMConfig
import numpy as np


def _make_client():
    """Instantiate and return an OpenAI client using configured env vars.

    The API key and base URL are read from `LLMConfig`.
    """
    api_key = LLMConfig.OPENAI_API_KEY_ENV
    base_url = LLMConfig.OPENAI_BASE_URL
    kwargs = {}
    if base_url:
        kwargs["base_url"] = base_url

    return OpenAI(api_key=api_key, **kwargs)


def llm_chat(prompt: str, model_key: str = "small", temperature: float | None = None, max_tokens: int | None = None) -> str:
    """Call the LLM chat/completions API and return the assistant text.

    Args:
     - prompt: The prompt or message content to send to the model.
     - model_key: Key name in `LLMConfig.MODELS` mapping, or a direct model id.
     - temperature: Optional temperature override for generation.
     - max_tokens: Optional max tokens limit for generation.

    Return:
     - The assistant-generated string content. May return the raw response
       string if parsing fails.
    """
    model = LLMConfig.MODELS.get(model_key, model_key)

    if temperature is None:
        temperature = LLMConfig.TEMPERATURE
    if max_tokens is None:
        max_tokens = LLMConfig.MAX_TOKENS

    client = _make_client()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )

    try:
        return response.choices[0].message.content.strip()
    except Exception:
        return str(response)


def llm_embed(text: str, model_key: str = "embed") -> list[float]:
    """Return an embedding vector (list[float]) for `text`.

    Args:
     - text: The input text to embed.
     - model_key: Key name in `LLMConfig.MODELS` mapping for embedding model.

    Return:
     - A list of floats representing the embedding, or an empty list on error.
    """
    model = LLMConfig.MODELS.get(model_key, model_key)
    client = _make_client()
    resp = client.embeddings.create(model=model, input=text)
    try:
        return resp.data[0].embedding
    except Exception:
        return []


def get_embedding_array(text: str) -> np.ndarray:
    """Get an embedding for `text` and return it as a NumPy float32 array.

    Args:
     - text: The input text to embed.

    Return:
     - A NumPy ndarray of dtype float32 with the embedding vector, or an
       empty ndarray if embedding failed.
    """
    vec = llm_embed(text)
    return np.array(vec, dtype="float32") if vec else np.array([], dtype="float32")
