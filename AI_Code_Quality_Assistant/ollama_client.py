import requests


def appel_ollama_generic(
    messages: list[dict],
    model: str,
    url: str,
    temp: float = 0.2,
    ctx: int = 8192,
) -> str | None:
    """
    Envoie une requête à l'API locale Ollama et retourne la réponse générée.

    Args:
        messages: Historique de conversation au format [{"role": ..., "content": ...}].
        model: Nom du modèle Ollama (ex: "qwen3-coder:30b").
        url: URL complète de l'endpoint (ex: "http://localhost:11434/api/chat").
        temp: Température de génération (0.0 = déterministe, 1.0 = créatif).
        ctx: Taille de la fenêtre de contexte en tokens.

    Returns:
        Texte généré par le modèle, ou None en cas d'erreur.
    """
    payload = {
        "model": model,
        "messages": messages,
        "options": {"temperature": temp, "num_ctx": ctx},
        "stream": False,
    }
    try:
        response = requests.post(url, json=payload, timeout=600)
        if response.status_code == 200:
            return response.json().get("message", {}).get("content", "")
        return None
    except Exception:
        return None
