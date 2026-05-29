import io
import re
import subprocess

import requests


def push_to_github(
    dossier_resultat: str,
    repo_url: str,
    token: str,
    nom_branche: str = "bot-refactoring",
) -> bool:
    """
    Initialise un dépôt Git local et pousse le code sur une branche GitHub.

    L'URL est modifiée pour inclure le PAT en HTTPS. Le push est forcé
    pour que la branche distante reflète exactement le dossier local.

    Args:
        dossier_resultat: Chemin du dossier contenant le code à envoyer.
        repo_url: URL du dépôt GitHub.
        token: Personal Access Token GitHub avec droits d'écriture.
        nom_branche: Nom de la branche cible.

    Returns:
        True si toutes les commandes Git ont réussi.

    Raises:
        Exception: En cas d'erreur d'authentification ou de commande Git.
    """
    try:
        if not repo_url.endswith(".git"):
            repo_url += ".git"
        url_avec_auth = repo_url.replace("https://", f"https://{token}@")

        commandes = [
            ["git", "init"],
            ["git", "checkout", "-b", nom_branche],
            ["git", "add", "."],
            ["git", "commit", "-m", "Refactoring et documentation automatiques"],
            ["git", "remote", "add", "origin", url_avec_auth],
            ["git", "push", "-u", "origin", nom_branche, "--force"],
        ]

        for cmd in commandes:
            result = subprocess.run(
                cmd, cwd=dossier_resultat, capture_output=True, text=True, check=False
            )
            if result.returncode != 0 and "nothing to commit" not in result.stdout:
                raise Exception(f"Erreur Git ({' '.join(cmd)}): {result.stderr}")

        return True
    except Exception as e:
        raise Exception(f"Échec du push GitHub: {e}")


def telecharger_repo_github(url: str) -> io.BytesIO:
    """
    Télécharge un dépôt GitHub public sous forme d'archive ZIP en mémoire.

    Args:
        url: URL du dépôt (ex: https://github.com/user/repo).

    Returns:
        Flux BytesIO contenant l'archive ZIP.

    Raises:
        ValueError: Si le format de l'URL est incorrect.
        Exception: Si le téléchargement échoue.
    """
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not match:
        raise ValueError("URL invalide. Format attendu : https://github.com/user/repo")

    owner, repo = match.groups()
    repo = repo.replace(".git", "")

    api_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
    response = requests.get(api_url, allow_redirects=True, timeout=30)

    if response.status_code == 200:
        return io.BytesIO(response.content)
    else:
        raise Exception(
            f"Erreur GitHub (Code {response.status_code}). "
            "Vérifiez l'URL ou si le dépôt est privé."
        )
