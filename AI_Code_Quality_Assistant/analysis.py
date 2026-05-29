import os
import sys
import ast
import glob

import networkx as nx
from pyvis.network import Network


def analyser_structure_complete(dossier: str) -> nx.DiGraph:
    """
    Analyse les dépendances d'un dossier Python et construit un graphe orienté.

    Les nœuds internes (fichiers locaux) sont en bleu, les dépendances externes
    en rouge. La stdlib est ignorée.

    Args:
        dossier: Chemin du répertoire contenant les fichiers .py.

    Returns:
        Graphe orienté NetworkX représentant l'architecture des dépendances.
    """
    G = nx.DiGraph()
    fichiers = glob.glob(os.path.join(dossier, "*.py"))
    modules_locaux = {os.path.splitext(os.path.basename(f))[0] for f in fichiers}
    std_lib = sys.stdlib_module_names if hasattr(sys, "stdlib_module_names") else set()

    for mod in modules_locaux:
        G.add_node(
            mod, type="internal", color="#4dabf7", title=f"Module Local: {mod}", shape="box"
        )

    for path in fichiers:
        current_module = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
            except Exception:
                continue

            for node in ast.walk(tree):
                target = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = alias.name.split(".")[0]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    target = node.module.split(".")[0]

                if target:
                    if target in modules_locaux:
                        G.add_edge(current_module, target, color="#888888")
                    elif target not in std_lib:
                        if target not in G:
                            G.add_node(
                                target,
                                type="external",
                                color="#ff8787",
                                title=f"Bibliotheque: {target}",
                                shape="ellipse",
                            )
                        G.add_edge(current_module, target, color="#ffb3b3", dashes=True)
    return G


def generer_graphe_interactif(G: nx.DiGraph, dossier_html: str) -> str | None:
    """
    Transforme un graphe NetworkX en une visualisation HTML interactive via Pyvis.

    Configure un affichage hiérarchique (haut → bas) avec un moteur de répulsion
    pour éviter le chevauchement.

    Args:
        G: Graphe orienté des dépendances.
        dossier_html: Répertoire où sauvegarder le fichier HTML.

    Returns:
        Nom du fichier généré ('dependances.html'), ou None si le graphe est vide.
    """
    if len(G.nodes) == 0:
        return None

    os.makedirs(dossier_html, exist_ok=True)
    chemin_html = os.path.join(dossier_html, "dependances.html")

    net = Network(
        height="600px", width="100%", bgcolor="#ffffff", font_color="black", directed=True
    )
    net.from_nx(G)

    net.set_options("""
    var options = {
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "nodeSpacing": 150
        }
      },
      "nodes": {
        "font": { "size": 16, "face": "tahoma" },
        "shadow": { "enabled": true }
      },
      "edges": {
        "color": { "inherit": true },
        "smooth": { "type": "cubicBezier", "forceDirection": "vertical", "roundness": 0.4 }
      },
      "physics": {
        "hierarchicalRepulsion": {
          "centralGravity": 0.0,
          "springLength": 100,
          "springConstant": 0.01,
          "nodeDistance": 120,
          "damping": 0.09
        },
        "solver": "hierarchicalRepulsion"
      }
    }
    """)

    try:
        net.save_graph(chemin_html)
        return "dependances.html"
    except Exception:
        return None
