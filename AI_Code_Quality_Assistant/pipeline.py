import os
import sys
import re
import glob
import shutil
import subprocess

import streamlit as st

from config import PROMPT_REFACTORING, PROMPT_COMMENTAIRES, PROMPT_README_GLOBAL, SOUS_DOSSIER_DOC
from parsers import parser_reponse_refactoring, decouper_reponse_commentaires
from utils import list_py_files, formater_str, generer_requirements
from ollama_client import appel_ollama_generic
from analysis import analyser_structure_complete, generer_graphe_interactif


def action_refactoriser(input_dir: str, model: str, url: str) -> str:
    """
    Restructure le code source via l'IA (création d'un main.py, encapsulation du code libre).

    Si le modèle échoue, copie simplement les fichiers originaux comme filet de sécurité.

    Args:
        input_dir: Répertoire contenant le code source original.
        model: Nom du modèle Ollama.
        url: URL de l'API Ollama.

    Returns:
        Chemin vers le répertoire contenant le code restructuré (_OUTPUT_REFACTOR).
    """
    base_dir = os.path.dirname(input_dir)
    out_dir = os.path.join(base_dir, "_OUTPUT_REFACTOR")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    files = list_py_files(input_dir)
    if not files:
        return out_dir

    contexte = ""
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            contexte += f"\n--- {os.path.basename(path)} ---\n{f.read()}\n"

    msgs = [
        {"role": "system", "content": PROMPT_REFACTORING},
        {"role": "user", "content": f"Fichiers :\n{contexte}"},
    ]

    st.info("Restructuration du code")
    res = appel_ollama_generic(msgs, model, url, ctx=16384)
    nouveaux = parser_reponse_refactoring(res)

    if not nouveaux:
        st.warning("L'IA n'a pas renvoyé de code valide. On garde les fichiers originaux.")
        shutil.copytree(input_dir, out_dir, dirs_exist_ok=True)
        return out_dir

    for nom, contenu in nouveaux.items():
        p = os.path.join(out_dir, nom)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(contenu)

    return out_dir


def action_formater(input_dir: str) -> str:
    """
    Applique le formatage Black sur tous les fichiers Python d'un dossier.

    Crée un nouveau répertoire _OUTPUT_FORMAT avec l'arborescence préservée.

    Args:
        input_dir: Répertoire contenant les fichiers à formater.

    Returns:
        Chemin vers le répertoire contenant le code formaté.
    """
    base_dir = os.path.dirname(input_dir) if "_OUTPUT" in input_dir else input_dir
    if "_OUTPUT" in os.path.basename(input_dir):
        base_dir = os.path.dirname(input_dir)

    out_dir = os.path.join(base_dir, "_OUTPUT_FORMAT")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    for path in list_py_files(input_dir):
        rel = os.path.relpath(path, input_dir)
        dst = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        with open(dst, "w", encoding="utf-8") as f:
            f.write(formater_str(code))

    return out_dir


def action_commenter_et_readme(input_dir: str, model: str, url: str) -> str:
    """
    Enrichit le code avec des docstrings/types via l'IA, génère un README et requirements.txt.

    Pour chaque fichier, extrait aussi les suggestions d'amélioration dans des NOTES_*.md.

    Args:
        input_dir: Répertoire contenant le code source à documenter.
        model: Nom du modèle Ollama.
        url: URL de l'API Ollama.

    Returns:
        Chemin vers le répertoire final (_OUTPUT_FINAL_CODE).
    """
    base_dir = os.path.dirname(input_dir)
    out_dir = os.path.join(base_dir, "_OUTPUT_FINAL_CODE")
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    files = list_py_files(input_dir)
    prog_bar = st.progress(0)
    all_code_context = ""

    for i, path in enumerate(files):
        rel = os.path.relpath(path, input_dir)
        filename = os.path.basename(path)

        with open(path, "r", encoding="utf-8") as f:
            code_orig = f.read()
        all_code_context += f"\n--- {filename} ---\n{code_orig}\n"

        msgs = [
            {"role": "system", "content": PROMPT_COMMENTAIRES},
            {"role": "user", "content": code_orig},
        ]

        res = appel_ollama_generic(msgs, model, url)

        final_code = code_orig
        suggestions_content = None

        if res:
            data = decouper_reponse_commentaires(res)
            if data["code"] and len(data["code"]) > 10:
                final_code = formater_str(data["code"])
            if data["suggest"]:
                suggestions_content = data["suggest"]

        # Écriture du fichier Python
        dst = os.path.join(out_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(final_code)

        # Écriture des suggestions
        if suggestions_content:
            base_name = os.path.splitext(filename)[0]
            notes_path = os.path.join(os.path.dirname(dst), f"NOTES_{base_name}.md")
            with open(notes_path, "w", encoding="utf-8") as f:
                f.write(f"# Notes pour {filename}\n\n{suggestions_content}")

        prog_bar.progress((i + 1) / (len(files) + 1))

    # Génération du README
    st.text("Generation du README.md")
    msgs_readme = [
        {"role": "system", "content": PROMPT_README_GLOBAL},
        {"role": "user", "content": all_code_context[:32000]},
    ]
    readme_content = appel_ollama_generic(msgs_readme, model, url, ctx=32000)
    if readme_content:
        with open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)

    generer_requirements(out_dir)
    prog_bar.progress(1.0)
    return out_dir


def action_doc_finale(input_dir: str) -> str:
    """
    Génère la documentation HTML (pdoc) et y intègre le graphe d'architecture interactif.

    Injecte le graphe en iframe dans l'index.html de pdoc, avec du CSS personnalisé.

    Args:
        input_dir: Répertoire contenant le code source finalisé.

    Returns:
        Chemin vers le répertoire final contenant le code et docs_html/.
    """
    base_dir = os.path.dirname(input_dir)
    out_dir = os.path.join(base_dir, "_OUTPUT_DOC")

    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    shutil.copytree(input_dir, out_dir, dirs_exist_ok=True)

    fichiers = glob.glob(os.path.join(out_dir, "*.py"))
    modules = [os.path.splitext(os.path.basename(f))[0] for f in fichiers]
    chemin_doc_html = os.path.join(out_dir, SOUS_DOSSIER_DOC)

    # 1. Documentation pdoc
    if modules:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.abspath(out_dir) + os.pathsep + env.get("PYTHONPATH", "")
        cmd = [sys.executable, "-m", "pdoc"] + modules + ["-o", SOUS_DOSSIER_DOC]
        try:
            subprocess.run(cmd, cwd=out_dir, env=env, capture_output=True)
        except Exception:
            pass

    # 2. Graphe d'architecture
    G = analyser_structure_complete(out_dir)
    nom_fichier_graph = generer_graphe_interactif(G, chemin_doc_html)

    # 3. CSS personnalisé
    style_custom = """
    <style>
        a[href^='https://pdoc.dev'], .pdoc-logo { display: none !important; }
        input[type="search"], input[placeholder*="Search"], #search, .search { display: none !important; }
        .graph-summary { transition: background-color 0.2s ease; }
        .graph-summary:hover { background-color: #f3f4f6 !important; }
    </style>
    """

    fichiers_html = glob.glob(os.path.join(chemin_doc_html, "**", "*.html"), recursive=True)

    # 4. Injection dans les fichiers HTML
    for html_file in fichiers_html:
        with open(html_file, "r", encoding="utf-8") as f:
            html = f.read()

        html = html.replace("Available Modules", "Modules du Projet")

        if "</head>" in html:
            html = html.replace("</head>", style_custom + "\n</head>")

        if nom_fichier_graph and os.path.basename(html_file) == "index.html":
            iframe_code = f"""
            <div style="margin: 1rem 0 3rem 0; font-family: system-ui, -apple-system, sans-serif;">
                <h1 style="font-size: 2.5em; color: #111827; margin-top: 0; margin-bottom: 0.5rem; font-weight: 700;">
                    Architecture du Projet
                </h1>
                <div style="border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff;
                            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); overflow: hidden;">
                    <details open>
                        <summary class="graph-summary" style="cursor: pointer; font-weight: 600;
                                    font-size: 1.1em; color: #374151; padding: 1.2rem 1.5rem;
                                    list-style: none; display: flex; justify-content: space-between;
                                    align-items: center; background-color: #f9fafb;
                                    border-bottom: 1px solid #e5e7eb;">
                            <span>Graphe des Dépendances (Interactif)</span>
                            <span style="font-size: 0.85em; color: #6b7280; font-weight: normal;">
                                Masquer / Afficher
                            </span>
                        </summary>
                        <div style="padding: 1.5rem; background: #ffffff;">
                            <iframe src="{nom_fichier_graph}" width="100%" height="700px"
                                    style="border: 1px solid #e5e7eb; border-radius: 6px;
                                           box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);">
                            </iframe>
                        </div>
                    </details>
                </div>
            </div>
            """

            if re.search(r"<main[^>]*>", html):
                html = re.sub(r"(<main[^>]*>)", r"\1\n" + iframe_code, html, count=1)
            elif re.search(r"<article[^>]*>", html):
                html = re.sub(r"(<article[^>]*>)", r"\1\n" + iframe_code, html, count=1)
            else:
                html = html.replace("<body>", "<body>\n" + iframe_code, 1)

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)

    return out_dir
