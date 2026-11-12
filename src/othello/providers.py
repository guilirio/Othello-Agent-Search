"""Provedor de LLM (Ollama local ou API) e utilitários independentes de provedor.

Configuração por variáveis de ambiente (ou por um arquivo .env na raiz do projeto):

    OTHELLO_PROVIDER      gemini (padrão) | groq | ollama
    OTHELLO_MODEL         nome do modelo (se omitido, usa o padrão do provedor)
    GOOGLE_API_KEY        chave do Gemini (provedor gemini)
    GROQ_API_KEY          chave do Groq (provedor groq)
    OTHELLO_MIN_INTERVAL  segundos mínimos entre chamadas (padrão: 4 em APIs, 0 no Ollama)
    OLLAMA_HOST           endpoint do Ollama (provedor ollama)

A chave nunca deve ser escrita no código nem versionada no Git.
Este módulo não importa bibliotecas pesadas no topo: o pacote de cada provedor
só é carregado quando o modelo é criado.
"""
import os
import re
import threading
import time
from pathlib import Path

DEFAULT_MODELS = {"ollama": "qwen2.5:3b", "gemini": "gemini-2.5-flash", "groq": "openai/gpt-oss-120b"}
PACKAGES = {"ollama": "langchain-ollama", "gemini": "langchain-google-genai", "groq": "langchain-groq"}
KEY_VARS = {"gemini": "GOOGLE_API_KEY", "groq": "GROQ_API_KEY"}


def load_dotenv(path) -> None:
    """Lê linhas CHAVE=valor de um .env sem sobrescrever variáveis já definidas no ambiente."""
    path = Path(path)
    try:
        if not path.is_file():
            return
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeDecodeError):
        return
    for line in lines:
        line = line.strip()
        if line.startswith("export "):
            line = line[7:].strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


for _folder in (Path.cwd(), Path(__file__).resolve().parent.parent.parent):
    load_dotenv(_folder / ".env")


def get_provider() -> str:
    provider = os.getenv("OTHELLO_PROVIDER", "gemini").strip().lower()
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"OTHELLO_PROVIDER inválido: '{provider}'. Use: {', '.join(DEFAULT_MODELS)}.")
    return provider


def default_model(provider: str | None = None) -> str:
    provider = provider or get_provider()
    return os.getenv("OTHELLO_MODEL") or DEFAULT_MODELS[provider]


def build_model(model_name: str | None = None, base_url: str | None = None):
    """Cria o cliente LangChain do provedor escolhido; erros claros se faltar chave ou pacote."""
    provider = get_provider()
    name = model_name or default_model(provider)
    if provider == "gemini" and not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
    key_var = KEY_VARS.get(provider)
    if key_var and not os.getenv(key_var):
        raise RuntimeError(f"Chave de API ausente: defina {key_var} (variável de ambiente ou arquivo .env).")
    try:
        if provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=name,
                base_url=base_url or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"),
                temperature=0, format="json", num_predict=512, num_ctx=16384,
                client_kwargs={"timeout": 120},
            )
        if provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=name, temperature=0, max_output_tokens=2048, timeout=120)
        from langchain_groq import ChatGroq
        # gpt-oss é modelo de raciocínio: os tokens de raciocínio contam no limite de saída,
        # então o teto precisa ser folgado para a resposta JSON não ser cortada.
        return ChatGroq(model=name, temperature=0, max_tokens=2048, timeout=120)
    except ImportError as exc:
        raise RuntimeError(
            f"Pacote ausente para o provedor '{provider}'. Instale com: pip install {PACKAGES[provider]}") from exc


def validate_provider(model_name: str | None = None) -> None:
    """Falha cedo (antes de rodar partidas) se faltar chave, pacote ou configuração."""
    build_model(model_name)


# --- Respostas -------------------------------------------------------------

def answer_text(answer) -> str:
    """Extrai o texto de uma resposta do LangChain (conteúdo pode ser str ou lista de partes)."""
    content = getattr(answer, "content", answer)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type", "text") == "text":
                parts.append(str(part.get("text", "")))
        return "".join(parts)
    return str(content)


def extract_json(text: str) -> str:
    """Remove cercas ```json ... ``` e texto ao redor, devolvendo o trecho entre { e }."""
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        text = text[start:end + 1]
    return text


# --- Limites de uso das APIs ----------------------------------------------

TRANSIENT_MARKERS = ("429", "rate limit", "rate_limit", "resource_exhausted", "quota",
                     "too many requests", "503", "unavailable", "overloaded", "timed out", "timeout")
DAILY_MARKERS = ("perday", "per day", "daily")


def is_transient(exc: Exception) -> bool:
    """Erro provavelmente temporário (limite por minuto, sobrecarga, timeout): vale esperar e tentar de novo."""
    return any(marker in str(exc).lower() for marker in TRANSIENT_MARKERS)


def is_daily_quota(exc: Exception) -> bool:
    """Cota diária esgotada: esperar alguns segundos não adianta."""
    return any(marker in str(exc).lower() for marker in DAILY_MARKERS)


def min_interval() -> float:
    default = 0.0 if get_provider() == "ollama" else 4.0
    try:
        return float(os.getenv("OTHELLO_MIN_INTERVAL", default))
    except ValueError:
        return default


_lock = threading.Lock()
_last_call = float("-inf")


def wait_turn() -> None:
    """Espaça as chamadas à API para respeitar o limite de requisições por minuto."""
    global _last_call
    interval = min_interval()
    if interval <= 0:
        return
    with _lock:
        delay = _last_call + interval - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        _last_call = time.monotonic()