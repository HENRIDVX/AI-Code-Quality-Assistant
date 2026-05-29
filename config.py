# Configuration générale
DEFAULT_MODEL = "qwen3-coder:30b"
DEFAULT_URL = "http://localhost:11434/api/chat"
SOUS_DOSSIER_DOC = "docs_html"

# Balises pour le parsing des réponses IA
BALISE_FILE_DEBUT = "<FILE name='"
BALISE_FILE_MILIEU = "'>"
BALISE_FILE_FIN = "</FILE>"

BALISE_CODE_DEBUT = "<CODE_SECTION>"
BALISE_CODE_FIN = "</CODE_SECTION>"
BALISE_SUGGEST_DEBUT = "<SUGGEST_SECTION>"
BALISE_SUGGEST_FIN = "</SUGGEST_SECTION>"

# Prompts système

PROMPT_REFACTORING = """
Tu es un architecte logiciel Python.
Ta mission : Créer un point d'entrée 'main.py' propre, SANS renommer les fichiers existants (sauf s'ils sont obsolètes).

RÈGLES STRICTES :
1. CONSERVATION : Garde les noms de fichiers originaux (ex: config.py, analysis.py doivent rester tels quels).
2. MAIN.PY : Crée un NOUVEAU fichier 'main.py'. C'est lui qui doit importer les autres fichiers et lancer la logique globale.
3. NETTOYAGE : Si un fichier exécute du code directement (code spaghetti), déplace ce code dans une fonction (ex: def run():) pour que 'main.py' puisse l'appeler proprement sans que le code se lance lors d'un import.
4. IMPORTS : Adapte les imports pour qu'ils fonctionnent avec le nouveau main.py.

Renvoie TOUS les fichiers du projet (les anciens modifiés et le nouveau main.py) au format XML ci-dessous.

FORMAT DE REPONSE :
<FILE name='nom_du_fichier.py'>
... code ...
</FILE>
"""

PROMPT_COMMENTAIRES = f"""
Tu es un développeur Python rigoureux.
Ta mission est d'ajouter des docstrings et des types (type hints) au code fourni.

IMPORTANT :
1. Tu dois renvoyer l'INTEGRALITE du code fichier, pas juste les modifications.
2. Ne change pas la logique.
3. Utilise IMPERATIVEMENT les balises ci-dessous.

{BALISE_CODE_DEBUT}
(Ici, colle tout le code python complet avec les docstrings ajoutées)
{BALISE_CODE_FIN}

{BALISE_SUGGEST_DEBUT}
(Une liste courte d'améliorations possibles pour ce fichier)
{BALISE_SUGGEST_FIN}
"""

PROMPT_README_GLOBAL = """
Tu dois rédiger un fichier README.md pour ce projet.
Voici tout le code du projet concaténé.

Le README doit contenir :
1. Le titre du projet.
2. Une description.
3. Comment l'installer (parler du requirements.txt).
4. Comment l'utiliser (lancer main.py).

Réponds seulement avec le contenu du fichier Markdown.
"""
