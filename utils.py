import os
import sys
import glob
import ast
import time
import zipfile
import tempfile
import io

import black
import importlib.metadata


# Dossiers à ignorer lors du scan de fichiers Python
IGNORE_DIRS = {
    "venv", ".venv", "__pycache__", "dist", "build", ".git",
    "_OUTPUT_FORMAT", "_OUTPUT_COMMENT", "_OUTPUT_DOC",
    "_OUTPUT_REFACTOR", "_OUTPUT_FINAL_CODE",
}


def list_py_files(root: str) -> list[str]:
    """
    Parcourt récursivement un répertoire pour lister tous les fichiers .py,
    en ignorant les dossiers non pertinents (venv, cache, outputs…).

    Args:
        root: Chemin du répertoire racine.

    Returns:
        Liste des chemins absolus des fichiers Python trouvés.
    """
    py_files = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fn in files:
            if fn.endswith(".py"):
                py_files.append(os.path.join(r, fn))
    return py_files


def formater_str(code_str: str) -> str:
    """
    Formate du code Python via Black. Retourne le code original si le formatage échoue.

    Args:
        code_str: Code source Python brut.

    Returns:
        Code formaté, ou code original en cas d'erreur de syntaxe.
    """
    try:
        return black.format_str(code_str, mode=black.Mode())
    except Exception:
        return code_str


def generer_requirements(dossier: str) -> None:
    """
    Génère un requirements.txt en analysant les imports du projet via l'AST.

    Filtre la stdlib et les modules locaux, puis tente de récupérer
    les versions installées pour figer les dépendances.

    Args:
        dossier: Chemin du répertoire contenant le projet Python.
    """
    imports_externes = set()
    std_lib = sys.stdlib_module_names if hasattr(sys, "stdlib_module_names") else set()
    fichiers_locaux = {
        os.path.splitext(os.path.basename(f))[0]
        for f in glob.glob(os.path.join(dossier, "*.py"))
    }

    for path in list_py_files(dossier):
        with open(path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    module_name = None
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_name = alias.name.split(".")[0]
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        module_name = node.module.split(".")[0]

                    if module_name and module_name not in std_lib and module_name not in fichiers_locaux:
                        imports_externes.add(module_name)
            except Exception:
                pass

    if imports_externes:
        with open(os.path.join(dossier, "requirements.txt"), "w", encoding="utf-8") as f:
            for imp in sorted(imports_externes):
                try:
                    version = importlib.metadata.version(imp)
                    f.write(f"{imp}=={version}\n")
                except importlib.metadata.PackageNotFoundError:
                    f.write(f"{imp}\n")


def unzip_to_temp(uploaded_file) -> str:
    """
    Extrait un fichier ZIP dans un répertoire temporaire.

    Détecte automatiquement si le contenu est encapsulé dans un dossier racine unique
    (cas classique des exports GitHub).

    Args:
        uploaded_file: Objet fichier provenant de st.file_uploader ou BytesIO.

    Returns:
        Chemin absolu vers le dossier contenant les fichiers extraits.
    """
    timestamp = int(time.time())
    tmpdir = tempfile.mkdtemp(prefix=f"projet_{timestamp}_")
    zip_path = os.path.join(tmpdir, "archive.zip")

    with open(zip_path, "wb") as f:
        f.write(
            uploaded_file.getvalue()
            if hasattr(uploaded_file, "getvalue")
            else uploaded_file.read()
        )

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(tmpdir)

    items = [x for x in os.listdir(tmpdir) if x != "archive.zip" and not x.startswith("__")]
    if len(items) == 1 and os.path.isdir(os.path.join(tmpdir, items[0])):
        return os.path.join(tmpdir, items[0])
    return tmpdir


def zip_folder(folder_path: str) -> bytes:
    """
    Compresse un répertoire entier en archive ZIP en mémoire (DEFLATE).

    Args:
        folder_path: Chemin du dossier à compresser.

    Returns:
        Contenu binaire de l'archive ZIP.
    """
    base = tempfile.mkdtemp(prefix="final_")
    zip_path = os.path.join(base, "rendu.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(folder_path):
            for fn in files:
                full = os.path.join(root, fn)
                z.write(full, os.path.relpath(full, folder_path))
    with open(zip_path, "rb") as f:
        return f.read()
