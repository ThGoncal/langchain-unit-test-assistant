"""
Interface Streamlit pour l'assistant de tests unitaires Python.

Consomme les deux API du projet :
- API auth (signup/login) : gestion de l'identité et du JWT.
- API assistant (analyze, generate_test, explain_test, full_pipeline, chat,
  history) : logique métier LangChain, appelée avec le token obtenu via l'API
  auth.

L'état de session (token, historique de chat affiché) est conservé dans
st.session_state, propre à chaque session utilisateur Streamlit — deux
onglets de navigateur distincts ont donc chacun leur propre authentification.
"""

import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# En Docker, ces URLs sont surchargées par docker-compose (noms de service
# "auth"/"main") ; en local, elles pointent par défaut sur localhost.
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8001")
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Assistant Tests Unitaires", page_icon="🧪", layout="wide")

# Initialisation de l'état de session — exécutée à chaque rerun du script
# (comportement normal de Streamlit), mais les valeurs ne sont réinitialisées
# que si les clés n'existent pas encore, donc l'état persiste bien entre les
# interactions de l'utilisateur au sein d'une même session.
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "chat_display" not in st.session_state:
    st.session_state.chat_display = []


def auth_headers() -> dict:
    """Construit le header Authorization à partir du token en session.

    Utilisé par tous les appels vers l'API assistant, qui exige un JWT
    valide (délégué à l'API auth via GET /me côté serveur).
    """
    return {"Authorization": f"Bearer {st.session_state.token}"}


def render_login_screen():
    """Affiche l'écran de connexion/inscription (API auth uniquement).

    Ne touche jamais à l'API assistant : cette fonction ne s'exécute que
    tant qu'aucun token n'est en session (voir main()).
    """
    st.title("🧪 Assistant de Tests Unitaires Python")
    st.caption("Analyse ton code, génère des tests pytest, discute avec l'assistant.")

    tab_login, tab_signup = st.tabs(["Connexion", "Inscription"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur", key="login_username")
            password = st.text_input("Mot de passe", type="password", key="login_password")
            if st.form_submit_button("Se connecter", use_container_width=True):
                try:
                    response = requests.post(
                        f"{AUTH_URL}/login",
                        json={"username": username, "password": password},
                        timeout=10,
                    )
                except requests.RequestException:
                    # API auth injoignable (conteneur down, mauvaise URL...) :
                    # distinct d'un mauvais mot de passe (géré ci-dessous).
                    st.error("Impossible de contacter l'API d'authentification.")
                else:
                    if response.status_code == 200:
                        st.session_state.token = response.json()["access_token"]
                        st.session_state.username = username
                        # Force un rerun immédiat : sans ça, l'utilisateur
                        # resterait affiché sur l'écran de connexion jusqu'à
                        # sa prochaine interaction avec l'app.
                        st.rerun()
                    else:
                        st.error(response.json().get("detail", "Échec de connexion."))

    with tab_signup:
        with st.form("signup_form"):
            username = st.text_input("Nom d'utilisateur", key="signup_username")
            password = st.text_input("Mot de passe", type="password", key="signup_password")
            if st.form_submit_button("Créer un compte", use_container_width=True):
                try:
                    response = requests.post(
                        f"{AUTH_URL}/signup",
                        json={"username": username, "password": password},
                        timeout=10,
                    )
                except requests.RequestException:
                    st.error("Impossible de contacter l'API d'authentification.")
                else:
                    if response.status_code == 200:
                        # Volontairement pas de connexion automatique après
                        # inscription : on laisse l'utilisateur passer par
                        # l'onglet Connexion, cohérent avec le flux attendu
                        # par test_auth_api.py (signup et login séparés).
                        st.success("Compte créé — connecte-toi dans l'onglet Connexion.")
                    else:
                        st.error(response.json().get("detail", "Échec de l'inscription."))


def render_analyze_tab():
    """Onglet /analyze : soumet un extrait de code, affiche le verdict is_optimal."""
    st.subheader("🔍 Analyser un code Python")
    code = st.text_area("Code à analyser", height=220, key="analyze_code",
                         placeholder="def add(a, b):\n    return a + b")
    if st.button("Analyser", key="analyze_btn", type="primary"):
        if not code.strip():
            st.warning("Colle du code avant de lancer l'analyse.")
            return
        with st.spinner("Analyse en cours..."):
            response = requests.post(f"{API_URL}/analyze", json={"code": code}, headers=auth_headers(), timeout=60)
        if response.status_code != 200:
            st.error(f"Erreur {response.status_code} : {response.text}")
            return
        result = response.json()
        # if/else explicite plutôt qu'un ternaire : une expression ternaire
        # utilisée comme instruction est interceptée par le "magic" de
        # Streamlit (toute expression seule sur sa ligne au niveau racine
        # d'une fonction appelée depuis le script principal peut être
        # transformée en st.write() implicite), ce qui affichait par erreur
        # le détail interne d'un DeltaGenerator au lieu du simple message.
        if result["is_optimal"]:
            st.success("✅ Code jugé optimal")
        else:
            st.warning("⚠️ Code jugé non optimal")
        if result["issues"]:
            st.markdown("**Problèmes identifiés :**")
            for issue in result["issues"]:
                st.markdown(f"- {issue}")
        if result["suggestions"]:
            st.markdown("**Suggestions :**")
            for suggestion in result["suggestions"]:
                st.markdown(f"- {suggestion}")


def render_generate_test_tab():
    """Onglet /generate_test : génère un test pytest pour un code donné.

    Le code et le test générés sont stockés en session (last_code/last_test)
    pour être repris automatiquement dans l'onglet "Expliquer un test",
    évitant à l'utilisateur de recopier le test manuellement.
    """
    st.subheader("🧪 Générer un test unitaire")
    code = st.text_area("Code à tester", height=220, key="gen_code",
                         placeholder="def add(a, b):\n    return a + b")
    if st.button("Générer le test", key="gen_btn", type="primary"):
        if not code.strip():
            st.warning("Colle du code avant de générer un test.")
            return
        with st.spinner("Génération en cours..."):
            response = requests.post(f"{API_URL}/generate_test", json={"code": code}, headers=auth_headers(), timeout=60)
        if response.status_code != 200:
            st.error(f"Erreur {response.status_code} : {response.text}")
            return
        unit_test = response.json()["unit_test"]
        st.session_state["last_code"] = code
        st.session_state["last_test"] = unit_test
        st.code(unit_test, language="python")
        st.caption("💡 Ce test est repris automatiquement dans l'onglet « Expliquer un test ».")


def render_explain_test_tab():
    """Onglet /explain_test : explique en langage naturel un couple (code, test).

    Les champs sont pré-remplis depuis last_code/last_test si l'utilisateur
    vient de générer un test dans l'onglet précédent, mais restent librement
    modifiables — on peut aussi coller un test écrit à la main.
    """
    st.subheader("📖 Expliquer un test unitaire")
    code = st.text_area("Code source", value=st.session_state.get("last_code", ""), height=160, key="explain_code")
    unit_test = st.text_area("Test unitaire", value=st.session_state.get("last_test", ""), height=160, key="explain_test_input")
    if st.button("Expliquer", key="explain_btn", type="primary"):
        if not code.strip() or not unit_test.strip():
            st.warning("Renseigne le code ET le test à expliquer.")
            return
        with st.spinner("Explication en cours..."):
            response = requests.post(
                f"{API_URL}/explain_test",
                json={"code": code, "unit_test": unit_test},
                headers=auth_headers(),
                timeout=60,
            )
        if response.status_code != 200:
            st.error(f"Erreur {response.status_code} : {response.text}")
            return
        st.info(response.json()["explanation"])


def render_full_pipeline_tab():
    """Onglet /full_pipeline : analyse, puis génère et explique si le code est optimal.

    Deux issues distinctes à afficher : arrêt anticipé (clé "error" dans la
    réponse, code jugé non optimal) ou pipeline complet (clés "test" et
    "explanation" présentes) — reflète directement la logique conditionnelle
    de l'endpoint côté API.
    """
    st.subheader("🚀 Pipeline complet (analyse → test → explication)")
    code = st.text_area("Code Python", height=220, key="pipeline_code",
                         placeholder='def add(a: int, b: int) -> int:\n    """Retourne la somme de a et b."""\n    return a + b')
    if st.button("Lancer le pipeline", key="pipeline_btn", type="primary"):
        if not code.strip():
            st.warning("Colle du code avant de lancer le pipeline.")
            return
        with st.spinner("Pipeline en cours (peut prendre quelques secondes)..."):
            response = requests.post(f"{API_URL}/full_pipeline", json={"code": code}, headers=auth_headers(), timeout=90)
        if response.status_code != 200:
            st.error(f"Erreur {response.status_code} : {response.text}")
            return
        result = response.json()
        if "error" in result:
            # Code jugé non optimal : le pipeline s'est arrêté après
            # l'analyse, pas de "test" ni "explanation" dans la réponse.
            st.warning(f"⛔ {result['error']} — le pipeline s'est arrêté après l'analyse.")
            analysis = result["analysis"]
            for issue in analysis["issues"]:
                st.markdown(f"- {issue}")
            if analysis["suggestions"]:
                st.markdown("**Suggestions :**")
                for suggestion in analysis["suggestions"]:
                    st.markdown(f"- {suggestion}")
        else:
            st.success("✅ Code optimal — test généré et expliqué")
            st.markdown("**Test unitaire généré :**")
            st.code(result["test"]["unit_test"], language="python")
            st.markdown("**Explication :**")
            st.info(result["explanation"]["explanation"])


def render_chat_tab():
    """Onglet /chat : conversation libre avec mémoire de contexte côté serveur.

    chat_display ne conserve que l'historique affiché dans CETTE session
    Streamlit (perdu au rechargement de la page) — à ne pas confondre avec
    /history, qui restitue l'historique persistant côté API pour l'utilisateur
    authentifié, quelle que soit la session de navigateur utilisée.
    """
    st.subheader("💬 Discuter avec l'assistant")
    for message in st.session_state.chat_display:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("Pose une question sur tes tests, ton code, pytest...")
    if user_input:
        st.session_state.chat_display.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        with st.chat_message("assistant"):
            with st.spinner("L'assistant réfléchit..."):
                response = requests.post(f"{API_URL}/chat", json={"input": user_input}, headers=auth_headers(), timeout=60)
            if response.status_code == 200:
                reply = response.json()["response"]
                st.markdown(reply)
                st.session_state.chat_display.append({"role": "assistant", "content": reply})
            else:
                st.error(f"Erreur {response.status_code} : {response.text}")


def render_history_tab():
    """Onglet /history : historique persistant côté serveur pour l'utilisateur courant.

    Rafraîchi uniquement sur clic (pas automatiquement à chaque interaction),
    pour éviter un appel réseau superflu à chaque rerun du script Streamlit.
    """
    st.subheader("🕓 Historique")
    if st.button("Rafraîchir l'historique", key="history_btn"):
        response = requests.get(f"{API_URL}/history", headers=auth_headers(), timeout=30)
        if response.status_code != 200:
            st.error(f"Erreur {response.status_code} : {response.text}")
            return
        history = response.json()["history"]
        if not history:
            st.info("Aucun échange enregistré pour l'instant.")
        for entry in history:
            role_label = "🧑 Toi" if entry["role"] == "user" else "🤖 Assistant"
            with st.expander(role_label):
                st.text(entry["content"])


def render_main_app():
    """Affiche l'application complète (sidebar + 6 onglets) une fois authentifié."""
    with st.sidebar:
        st.markdown(f"### 👋 {st.session_state.username}")
        if st.button("Se déconnecter", use_container_width=True):
            # Réinitialise l'état de session ; ne révoque pas le JWT côté
            # serveur (aucun mécanisme de révocation — voir README, section
            # Pistes d'amélioration), il reste techniquement valide jusqu'à
            # expiration naturelle mais n'est simplement plus utilisé ici.
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.chat_display = []
            st.rerun()

    st.title("🧪 Assistant de Tests Unitaires Python")

    tabs = st.tabs(["Analyser", "Générer un test", "Expliquer un test", "Pipeline complet", "Chat", "Historique"])
    with tabs[0]:
        render_analyze_tab()
    with tabs[1]:
        render_generate_test_tab()
    with tabs[2]:
        render_explain_test_tab()
    with tabs[3]:
        render_full_pipeline_tab()
    with tabs[4]:
        render_chat_tab()
    with tabs[5]:
        render_history_tab()


def main():
    """Point d'entrée : écran de connexion ou application complète selon l'état du token."""
    if st.session_state.token is None:
        render_login_screen()
    else:
        render_main_app()


# Assignation à `_` plutôt qu'un simple appel `main()` : empêche le "magic"
# de Streamlit d'intercepter cette expression de niveau racine et de tenter
# un st.write() implicite sur sa valeur de retour (voir commentaire dans
# render_analyze_tab pour le contexte complet de ce bug rencontré en
# développement).
_ = main()