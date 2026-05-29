import streamlit as st

from config import DEFAULT_MODEL, DEFAULT_URL
from utils import unzip_to_temp, zip_folder
from github_integration import push_to_github, telecharger_repo_github
from pipeline import (
    action_refactoriser,
    action_formater,
    action_commenter_et_readme,
    action_doc_finale,
)


def main():
    """Point d'entrée de l'interface Streamlit."""

    # Configuration de la page 
    st.set_page_config(
        page_title="Outil d'Analyse et Restructuration Python",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    #  Sidebar : paramètres 
    with st.sidebar:
        st.header("Configuration du Traitement")
        st.markdown("---")

        st.subheader("Paramètres API")
        ollama_model = st.text_input("Modèle cible", value=DEFAULT_MODEL)
        ollama_url = st.text_input("URL de l'API", value=DEFAULT_URL)

        st.markdown("---")
        st.subheader("Intégration GitHub")
        github_token = st.text_input(
            "Token GitHub (PAT) (Optionnel)",
            type="password",
            help="Nécessaire uniquement pour repousser le code modifié sur GitHub.",
        )

        st.markdown("---")
        st.subheader("Paramètres de sortie")
        output_name = st.text_input("Nom de l'archive générée", value="Projet_Restructure")

    #  En-tête 
    st.title("Analyse et Restructuration de Projet Python")
    st.markdown(
        "Cette application permet de normaliser, documenter et analyser l'architecture "
        "d'un code source Python en s'appuyant sur des outils d'analyse statique et "
        "des modèles de langage."
    )
    st.divider()

    #  1. Importation 
    st.header("1. Importation du code source")
    tab_zip, tab_github = st.tabs(["Fichier ZIP", "Dépôt GitHub"])

    with tab_zip:
        uploaded = st.file_uploader(
            "Veuillez charger un dossier ZIP contenant le projet Python à analyser.",
            type=["zip"],
        )
        if uploaded:
            file_id = f"{uploaded.name}_{uploaded.size}"
            if st.session_state.get("current_file_id") != file_id:
                st.session_state.current_file_id = file_id
                st.session_state.project_path = unzip_to_temp(uploaded)
                st.session_state.source_info = f"Dossier ZIP chargé : {uploaded.name}"

    with tab_github:
        github_url = st.text_input("URL du dépôt GitHub")
        if github_url and st.button("Télécharger le dépôt"):
            with st.spinner("Téléchargement du dépôt depuis GitHub."):
                try:
                    source_donnees = telecharger_repo_github(github_url)
                    st.session_state.current_file_id = github_url
                    st.session_state.project_path = unzip_to_temp(source_donnees)
                    st.session_state.source_info = "Dépôt GitHub chargé."
                except Exception as e:
                    st.error(str(e))

    if not st.session_state.get("project_path"):
        return

    st.success(st.session_state.get("source_info", "Projet chargé avec succès."))
    projet_dir = st.session_state.project_path

    #  2. Options 
    st.header("2. Options d'exécution")
    do_refactor = st.checkbox("Activer la restructuration", value=True)

    #  3. Exécution 
    st.header("3. Lancement du pipeline de traitement")

    if st.button("Lancer le traitement", type="primary"):
        curr = projet_dir

        try:
            with st.status("Exécution en cours", expanded=True) as status:
                if do_refactor:
                    st.write("Etape 1/4 : Restructuration du code")
                    curr = action_refactoriser(curr, ollama_model, ollama_url)

                st.write("Etape 2/4 : Formatage du code")
                curr = action_formater(curr)

                st.write("Etape 3/4 : Ajout des commentaires et du Readme")
                curr = action_commenter_et_readme(curr, ollama_model, ollama_url)

                st.write("Etape 4/4 : Generation de la documentation et du graphe")
                final = action_doc_finale(curr)

                status.update(
                    label="Processus de traitement terminé avec succès.",
                    state="complete",
                    expanded=False,
                )

            st.session_state.result_path = final

        except Exception as e:
            st.error(f"Une exception a été levée lors du traitement : {e}")

    #  4. Résultats 
    if not st.session_state.get("result_path"):
        return

    st.info("Traitement terminé.")
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="Télécharger le résultat (ZIP)",
            data=zip_folder(st.session_state.result_path),
            file_name=f"{output_name}.zip",
            mime="application/zip",
            type="primary",
        )

    if st.session_state.current_file_id.startswith("http"):
        with col2:
            if st.button("Push sur GitHub"):
                if not github_token:
                    st.error("Veuillez entrer un Token GitHub dans le panneau latéral gauche.")
                else:
                    with st.spinner("Envoi du code vers GitHub"):
                        try:
                            push_to_github(
                                dossier_resultat=st.session_state.result_path,
                                repo_url=st.session_state.current_file_id,
                                token=github_token,
                            )
                            st.success("Code envoyé sur la branche `bot-refactoring` !")
                        except Exception as e:
                            st.error(str(e))


if __name__ == "__main__":
    main()
