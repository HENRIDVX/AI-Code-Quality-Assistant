from config import (
    BALISE_FILE_DEBUT,
    BALISE_FILE_MILIEU,
    BALISE_FILE_FIN,
    BALISE_CODE_DEBUT,
    BALISE_CODE_FIN,
    BALISE_SUGGEST_DEBUT,
    BALISE_SUGGEST_FIN,
)


def parser_reponse_refactoring(texte: str) -> dict:
    """
    Extrait les noms de fichiers et leur code source depuis la réponse de l'IA.

    Cherche des blocs encadrés par les balises <FILE name='...'> et nettoie
    le formatage Markdown superflu.

    Args:
        texte: La réponse brute renvoyée par l'API.

    Returns:
        Dictionnaire {nom_fichier: code_source}. Vide si rien n'est trouvé.
    """
    fichiers = {}
    if not texte:
        return fichiers

    parts = texte.split(BALISE_FILE_DEBUT)
    for part in parts[1:]:
        try:
            if BALISE_FILE_MILIEU in part and BALISE_FILE_FIN in part:
                header, reste = part.split(BALISE_FILE_MILIEU, 1)
                nom_fichier = header.strip()
                contenu = reste.split(BALISE_FILE_FIN)[0].strip()
                contenu = contenu.replace("```python", "").replace("```", "")
                fichiers[nom_fichier] = contenu
        except Exception:
            continue
    return fichiers


def decouper_reponse_commentaires(texte_complet: str) -> dict:
    """
    Extrait le code et les suggestions d'amélioration depuis la réponse de l'IA.

    Tente d'abord une extraction via les balises strictes (<CODE_SECTION>),
    puis un fallback sur les blocs Markdown ```python si besoin.

    Args:
        texte_complet: La réponse brute du modèle.

    Returns:
        Dictionnaire avec les clés "code" (str | None) et "suggest" (str | None).
    """
    resultats = {"code": None, "suggest": None}
    if not texte_complet:
        return resultats

    # 1. Extraction via balises strictes
    try:
        if BALISE_CODE_DEBUT in texte_complet and BALISE_CODE_FIN in texte_complet:
            parts = texte_complet.split(BALISE_CODE_DEBUT)[1].split(BALISE_CODE_FIN)
            resultats["code"] = parts[0].strip().replace("```python", "").replace("```", "")

        if BALISE_SUGGEST_DEBUT in texte_complet and BALISE_SUGGEST_FIN in texte_complet:
            resultats["suggest"] = (
                texte_complet.split(BALISE_SUGGEST_DEBUT)[1]
                .split(BALISE_SUGGEST_FIN)[0]
                .strip()
            )
    except Exception:
        pass

    # 2. Fallback : bloc Markdown
    if not resultats["code"] and "```python" in texte_complet:
        try:
            parts = texte_complet.split("```python")[1].split("```")[0]
            resultats["code"] = parts.strip()
        except Exception:
            pass

    return resultats
