import os
import random
import threading
import secrets

from dotenv import load_dotenv

from werkzeug.security import generate_password_hash, check_password_hash

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    session,
    redirect
)

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")


from core import (
    creer_joueur,
    niveau,
    lancer_de as core_lancer_de,
    choisir_carte,
    tirer_carte as core_tirer_carte,
    appliquer_effet,
    traiter_reponse,
    verifier_victoire,
)


from database import (
    creer_base,
    enregistrer_joueur,
    mettre_a_jour_joueur,
    ajouter_partie,
    ajouter_victoire,
    enregistrer_score,
    classement,
    creer_table_utilisateurs_web,
    creer_utilisateur_web,
    obtenir_utilisateur_web,
)


# ============================================================
# CONFIGURATION
# ============================================================

TAILLE_PLATEAU = 30

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "cle-secrete-pour-defi-reflexion"
)


# ============================================================
# ACCUEIL WEB
# ============================================================

@app.route("/")
def accueil():

    utilisateur_connecte = session.get(
        "web_user"
    )

    return render_template(
        "index.html",
        utilisateur_connecte=utilisateur_connecte
    )


# ============================================================
# ADMINISTRATION
# ============================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "1234"
)


# ============================================================
# INSCRIPTION
# ============================================================

@app.route(
    "/inscription",
    methods=["GET", "POST"]
)
def inscription():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        password_confirm = request.form.get(
            "password_confirm",
            ""
        )

        if not username or not password:

            return render_template(
                "inscription.html",
                erreur=(
                    "❌ Tous les champs "
                    "sont obligatoires."
                )
            )

        if password != password_confirm:

            return render_template(
                "inscription.html",
                erreur=(
                    "❌ Les mots de passe "
                    "ne correspondent pas."
                )
            )

        if len(password) < 4:

            return render_template(
                "inscription.html",
                erreur=(
                    "❌ Le mot de passe doit "
                    "contenir au moins 4 caractères."
                )
            )

        password_hash = generate_password_hash(
            password
        )

        succes = creer_utilisateur_web(
            username,
            password_hash
        )

        if not succes:

            return render_template(
                "inscription.html",
                erreur=(
                    "❌ Ce nom d'utilisateur "
                    "existe déjà."
                )
            )

        utilisateur = obtenir_utilisateur_web(
            username
        )

        if not utilisateur:

            return render_template(
                "inscription.html",
                erreur=(
                    "❌ Impossible de créer "
                    "le compte."
                )
            )

        session["web_user"] = username
        session["web_id"] = utilisateur[0]

        return redirect("/")

    return render_template(
        "inscription.html"
    )


# ============================================================
# CONNEXION
# ============================================================

@app.route(
    "/connexion",
    methods=["GET", "POST"]
)
def connexion():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        utilisateur = obtenir_utilisateur_web(
            username
        )

        if utilisateur and check_password_hash(
            utilisateur[2],
            password
        ):

            session["web_user"] = utilisateur[1]
            session["web_id"] = utilisateur[0]

            return redirect("/")

        return render_template(
            "connexion.html",
            erreur=(
                "❌ Nom d'utilisateur "
                "ou mot de passe incorrect."
            )
        )

    return render_template(
        "connexion.html"
    )


# ============================================================
# DECONNEXION
# ============================================================

@app.route("/deconnexion")
def deconnexion():

    session.pop(
        "web_user",
        None
    )

    session.pop(
        "web_id",
        None
    )

    return redirect("/")


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            session["admin"] = True

            return redirect("/admin")

        return render_template(
            "admin_login.html",
            erreur=(
                "❌ Identifiant ou "
                "mot de passe incorrect."
            )
        )

    return render_template(
        "admin_login.html"
    )


# ============================================================
# ADMIN
# ============================================================

@app.route("/admin")
def admin():

    if not session.get("admin"):

        return redirect(
            "/admin/login"
        )

    joueurs = classement(50)

    return render_template(
        "admin.html",
        joueurs=joueurs
    )


# ============================================================
# DECONNEXION ADMIN
# ============================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin",
        None
    )

    return redirect(
        "/admin/login"
    )


# ============================================================
# CLASSEMENT WEB
# ============================================================

@app.route("/classement")
def page_classement():

    joueurs = classement(50)

    return render_template(
        "classement.html",
        joueurs=joueurs
    )


# ============================================================
# PARTIES WEB
# ============================================================

web_parties = {}


# ============================================================
# JOUEUR WEB
# ============================================================

def get_web_player():

    web_id = session.get(
        "web_id"
    )

    if not web_id:

        web_id = secrets.token_hex(
            16
        )

        session["web_id"] = web_id

    username = session.get(
        "web_user",
        "Joueur Web"
    )

    if web_id not in web_parties:

        joueur = creer_joueur(
            web_id,
            username,
            username
        )

        web_parties[web_id] = joueur

    return web_parties[web_id]


# ============================================================
# ETAT DU JOUEUR WEB
# ============================================================

def etat_joueur_web(joueur):

    return {
        "nom": joueur.get(
            "nom",
            "Joueur Web"
        ),

        "position": joueur.get(
            "position",
            1
        ),

        "vies": joueur.get(
            "vies",
            3
        ),

        "points": joueur.get(
            "points",
            0
        ),

        "jetons": joueur.get(
            "jetons",
            0
        ),

        "serie": joueur.get(
            "serie",
            0
        ),

        "niveau": niveau(joueur)
    }


# ============================================================
# API WEB — DEMARRER UNE PARTIE
# ============================================================

@app.route(
    "/api/start",
    methods=["POST"]
)
def api_start():

    joueur = get_web_player()

    nouveau_joueur = creer_joueur(
        session["web_id"],
        session.get(
            "web_user",
            "Joueur Web"
        ),
        session.get(
            "web_user"
        )
    )

    web_parties[
        session["web_id"]
    ] = nouveau_joueur

    joueur = nouveau_joueur

    return jsonify({
        "success": True,

        "message":
            "🎮 Nouvelle partie !",

        "joueur":
            etat_joueur_web(joueur)
    })


# ============================================================
# API WEB — LANCER LE DE
# ============================================================

@app.route(
    "/api/dice",
    methods=["POST"]
)
def api_dice():

    joueur = get_web_player()

    # --------------------------------------------------------
    # Vérifier les vies
    # --------------------------------------------------------

    if joueur.get(
        "vies",
        0
    ) <= 0:

        return jsonify({
            "success": False,
            "message":
                "💀 Tu n'as plus de vies."
        }), 400


    # --------------------------------------------------------
    # Vérifier une question en cours
    # --------------------------------------------------------

    if "carte" in joueur:

        return jsonify({
            "success": False,
            "message":
                "🧠 Réponds d'abord "
                "à la question en cours."
        }), 400


    # --------------------------------------------------------
    # Lancer le dé
    # --------------------------------------------------------

    resultat = core_lancer_de(
        joueur
    )

    de = resultat["de"]

    ancienne_position = (
        resultat["ancienne_position"]
    )

    nouvelle_position = (
        resultat["nouvelle_position"]
    )


    # --------------------------------------------------------
    # Victoire immédiate
    # --------------------------------------------------------

    if verifier_victoire(joueur):

        ajouter_victoire(
            joueur["id"],
            joueur["points"],
            joueur["jetons"]
        )

        return jsonify({

            "success": True,

            "victoire": True,

            "de": de,

            "ancienne_position":
                ancienne_position,

            "nouvelle_position":
                nouvelle_position,

            "message":
                "🏆 VICTOIRE ! "
                "Tu as atteint la case 30 !",

            "joueur":
                etat_joueur_web(joueur)
        })


    # --------------------------------------------------------
    # Tirer une carte
    # --------------------------------------------------------

    type_carte = choisir_carte()


    # ========================================================
    # QUESTION OU DEFI
    # ========================================================

    if type_carte in [
        "QUESTION",
        "DEFI"
    ]:

        carte = core_tirer_carte(
            type_carte
        )

        joueur["carte"] = carte

        return jsonify({

            "success": True,

            "victoire": False,

            "type": type_carte,

            "de": de,

            "ancienne_position":
                ancienne_position,

            "nouvelle_position":
                nouvelle_position,

            "question":
                carte["question"],

            "reponses":
                carte["reponses"],

            "message":
                "🧠 Réponds à la question !",

            "joueur":
                etat_joueur_web(joueur)
        })


    # ========================================================
    # CHANCE
    # ========================================================

    if type_carte == "CHANCE":

        carte = core_tirer_carte(
            "CHANCE"
        )

        action, valeur, texte = carte

        appliquer_effet(
            joueur,
            action,
            valeur
        )

        victoire = verifier_victoire(
            joueur
        )

        if victoire:

            ajouter_victoire(
                joueur["id"],
                joueur["points"],
                joueur["jetons"]
            )

        return jsonify({

            "success": True,

            "victoire": victoire,

            "type": "CHANCE",

            "de": de,

            "ancienne_position":
                ancienne_position,

            "nouvelle_position":
                joueur["position"],

            "message": texte,

            "joueur":
                etat_joueur_web(joueur)
        })


    # ========================================================
    # PIEGE
    # ========================================================

    if type_carte == "PIEGE":

        carte = core_tirer_carte(
            "PIEGE"
        )

        action, valeur, texte = carte

        appliquer_effet(
            joueur,
            action,
            valeur
        )

        # Vérifier si le piège provoque
        # éventuellement une victoire
        victoire = verifier_victoire(
            joueur
        )

        return jsonify({

            "success": True,

            "victoire": victoire,

            "type": "PIEGE",

            "de": de,

            "ancienne_position":
                ancienne_position,

            "nouvelle_position":
                joueur["position"],

            "message": texte,

            "joueur":
                etat_joueur_web(joueur)
        })


    # --------------------------------------------------------
    # Type inconnu
    # --------------------------------------------------------

    return jsonify({

        "success": False,

        "message":
            "❌ Type de carte inconnu."

    }), 500


# ============================================================
# API WEB — REPONDRE A UNE QUESTION
# ============================================================

@app.route(
    "/api/answer",
    methods=["POST"]
)
def api_answer():

    joueur = get_web_player()


    # --------------------------------------------------------
    # Vérifier qu'une question est en cours
    # --------------------------------------------------------

    if "carte" not in joueur:

        return jsonify({

            "success": False,

            "message":
                "❌ Aucune question en cours."

        }), 400


    # --------------------------------------------------------
    # Récupérer les données JSON
    # --------------------------------------------------------

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    choix = data.get(
        "choix"
    )

    print(
        "📩 Réponse reçue :",
        repr(choix)
    )


    # --------------------------------------------------------
    # Récupérer la carte
    # --------------------------------------------------------

    carte = joueur["carte"]

    reponses = carte.get(
        "reponses",
        []
    )


    if not reponses:

        return jsonify({

            "success": False,

            "message":
                "❌ Aucune réponse disponible."

        }), 400


    # ========================================================
    # CONVERSION DE LA REPONSE
    # ========================================================

    try:

        # ----------------------------------------------------
        # Cas 1 :
        # Le navigateur envoie directement un nombre
        # ----------------------------------------------------

        if isinstance(
            choix,
            int
        ):

            index_choix = choix


        # ----------------------------------------------------
        # Cas 2 :
        # Le navigateur envoie du texte
        # ----------------------------------------------------

        elif isinstance(
            choix,
            str
        ):

            choix_nettoye = (
                choix.strip()
            )

            # Essayer de convertir
            # en nombre
            try:

                index_choix = int(
                    choix_nettoye
                )

            except ValueError:

                # Rechercher le texte
                # dans les réponses

                index_choix = -1

                for i, reponse in enumerate(
                    reponses
                ):

                    if (
                        str(reponse).strip()
                        == choix_nettoye
                    ):

                        index_choix = i

                        break


        else:

            index_choix = -1


    except Exception as e:

        print(
            "❌ Erreur conversion réponse :",
            repr(e)
        )

        return jsonify({

            "success": False,

            "message":
                "❌ Réponse invalide."

        }), 400


    # ========================================================
    # VERIFIER L'INDEX
    # ========================================================

    if (
        index_choix < 0
        or index_choix >= len(
            reponses
        )
    ):

        print(
            "❌ Réponse inconnue :",
            repr(choix)
        )

        print(
            "📋 Réponses disponibles :",
            reponses
        )

        return jsonify({

            "success": False,

            "message":
                "❌ Cette réponse n'existe pas."

        }), 400


    # ========================================================
    # TRAITER LA REPONSE
    # ========================================================

    try:

        resultat = traiter_reponse(
            joueur,
            carte,
            index_choix
        )

    except Exception as e:

        print(
            "❌ Erreur dans "
            "traiter_reponse :",
            repr(e)
        )

        return jsonify({

            "success": False,

            "message":
                "❌ Erreur lors du traitement "
                "de la réponse."

        }), 500


    # ========================================================
    # MESSAGE DE REPONSE
    # ========================================================

    if resultat["correct"]:

        message = (
            "✅ Bonne réponse ! "
            f"+{resultat['points_gagnes']} points"
        )

        if resultat["bonus"] > 0:

            message += (
                " 🔥 Bonus de série !"
            )

    else:

        bonne_reponse = reponses[
            carte["bonne"]
        ]

        message = (
            "❌ Mauvaise réponse ! "
            "La bonne réponse était : "
            f"{bonne_reponse}"
        )


    # --------------------------------------------------------
    # Supprimer la carte
    # --------------------------------------------------------

    joueur.pop(
        "carte",
        None
    )


    # --------------------------------------------------------
    # Vérifier victoire
    # --------------------------------------------------------

    victoire = verifier_victoire(
        joueur
    )


    # ========================================================
    # GAME OVER
    # ========================================================

    if joueur["vies"] <= 0:

        enregistrer_score(
            joueur["id"],
            joueur["points"],
            joueur["jetons"]
        )

        message += (
            " 💀 GAME OVER !"
        )

        return jsonify({

            "success": True,

            "game_over": True,

            "correct":
                resultat["correct"],

            "points_gagnes":
                resultat["points_gagnes"],

            "bonus":
                resultat["bonus"],

            "vies_perdues":
                resultat["vies_perdues"],

            "serie":
                resultat["serie"],

            "jetons_gagnes":
                resultat["jetons_gagnes"],

            "victoire":
                False,

            "message":
                message,

            "joueur":
                etat_joueur_web(joueur)
        })


    # ========================================================
    # VICTOIRE
    # ========================================================

    if victoire:

        ajouter_victoire(
            joueur["id"],
            joueur["points"],
            joueur["jetons"]
        )

        message += (
            " 🏆 VICTOIRE !"
        )


    # ========================================================
    # REPONSE NORMALE
    # ========================================================

    return jsonify({

        "success": True,

        "game_over": False,

        "correct":
            resultat["correct"],

        "points_gagnes":
            resultat["points_gagnes"],

        "bonus":
            resultat["bonus"],

        "vies_perdues":
            resultat["vies_perdues"],

        "serie":
            resultat["serie"],

        "jetons_gagnes":
            resultat["jetons_gagnes"],

        "victoire":
            victoire,

        "message":
            message,

        "joueur":
            etat_joueur_web(joueur)
    })


# ============================================================
# SERVEUR FLASK
# ============================================================

def lancer_serveur():

    creer_base()

    creer_table_utilisateurs_web()

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )


# ============================================================
# PARTIES TELEGRAM
# ============================================================

parties = {}


# ============================================================
# AFFICHER LE JOUEUR
# ============================================================

def texte_joueur(joueur):

    username = joueur.get(
        "username"
    )

    if username:

        identifiant = (
            f"@{username}"
        )

    else:

        identifiant = (
            "Aucun username"
        )

    return (

        f"👤 {joueur['nom']}\n"

        f"🔹 {identifiant}\n\n"

        f"📍 Case : "
        f"{joueur['position']}/"
        f"{TAILLE_PLATEAU}\n"

        f"❤️ Vies : "
        f"{joueur['vies']}\n"

        f"⭐ Points : "
        f"{joueur['points']}\n"

        f"🪙 Jetons : "
        f"{joueur['jetons']}\n"

        f"🔥 Série : "
        f"{joueur['serie']}\n"

        f"🏅 Niveau : "
        f"{niveau(joueur)}"
    )


# ============================================================
# CLAVIER DU JEU
# ============================================================

def clavier_jeu():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "🎲 Lancer le dé",
                callback_data="de"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 Mon profil",
                callback_data="profil"
            )
        ],

        [
            InlineKeyboardButton(
                "🛑 Abandonner",
                callback_data="stop"
            )
        ]

    ])


# ============================================================
# CLAVIER PRINCIPAL
# ============================================================

clavier = InlineKeyboardMarkup([

    [
        InlineKeyboardButton(
            "🎮 JOUER",
            callback_data="nouvelle_partie"
        )
    ],

    [
        InlineKeyboardButton(
            "🏆 CLASSEMENT",
            callback_data="classement"
        )
    ],

    [
        InlineKeyboardButton(
            "📜 RÈGLES",
            callback_data="regles"
        )
    ]

])


# ============================================================
# START TELEGRAM
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "🎲 *DÉFI RÉFLEXION*\n\n"

        "Bienvenue ! 🧠\n\n"

        "Atteins la case 30 pour gagner !\n\n"

        "❤️ 3 vies\n"
        "⭐ Points\n"
        "🪙 Jetons\n"
        "🔥 Séries\n"
        "🧠 Questions\n"
        "⚡ Défis\n"
        "🍀 Chance\n"
        "🪤 Pièges",

        parse_mode="Markdown",

        reply_markup=clavier
    )


# ============================================================
# JOUER TELEGRAM
# ============================================================

async def jouer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    nom = (
        user.first_name
        or "Joueur"
    )

    username = user.username

    enregistrer_joueur(
        user.id,
        username,
        nom
    )

    mettre_a_jour_joueur(
        user.id,
        username,
        nom
    )

    ajouter_partie(
        user.id
    )

    joueur = creer_joueur(
        user.id,
        nom,
        username
    )

    parties[user.id] = joueur

    await update.message.reply_text(

        "🎮 *NOUVELLE PARTIE !*\n\n"

        "📍 Tu commences à la case 1.\n"
        "❤️ Vies : 3\n"
        "⭐ Points : 0\n"
        "🪙 Jetons : 0\n\n"

        "🎯 Objectif : atteindre la case 30 !",

        parse_mode="Markdown",

        reply_markup=clavier_jeu()
    )


# ============================================================
# REGLES TELEGRAM
# ============================================================

async def regles(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(

        "📜 *RÈGLES DE DÉFI RÉFLEXION*\n\n"

        "🎯 Atteins la case 30.\n\n"

        "🎲 Lance le dé à chaque tour.\n\n"

        "🧠 Réponds aux questions.\n\n"

        "⚡ Relève les défis.\n\n"

        "🍀 Chance : bonus de points ou déplacement.\n\n"

        "🪤 Piège : perte de points ou recul.\n\n"

        "❤️ Une mauvaise réponse fait perdre 1 vie.\n\n"

        "🔥 3 bonnes réponses consécutives "
        "donnent un bonus.\n\n"

        "🪙 Les bonnes réponses donnent des jetons.",

        parse_mode="Markdown"
    )


# ============================================================
# LANCER LE DE TELEGRAM
# ============================================================

async def lancer_de(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    if user_id not in parties:

        await query.edit_message_text(

            "❌ Tu n'as pas de partie "
            "en cours.\n\n"

            "Utilise /jouer pour commencer."
        )

        return

    joueur = parties[user_id]

    if "carte" in joueur:

        await query.edit_message_text(

            "🧠 Tu dois d'abord "
            "répondre à la question."
        )

        return

    resultat = core_lancer_de(
        joueur
    )

    de = resultat["de"]

    ancienne_position = (
        resultat["ancienne_position"]
    )

    nouvelle_position = (
        resultat["nouvelle_position"]
    )

    message = (

        "🎲 *LANCER DU DÉ*\n\n"

        f"🎲 Résultat : *{de}*\n\n"

        f"📍 Case : "
        f"{ancienne_position} ➡️ "
        f"*{nouvelle_position}*\n\n"
    )


    # --------------------------------------------------------
    # VICTOIRE
    # --------------------------------------------------------

    if verifier_victoire(joueur):

        ajouter_victoire(
            joueur["id"],
            joueur["points"],
            joueur["jetons"]
        )

        message += (

            "🏆 *VICTOIRE !* 🏆\n\n"

            f"🎉 {joueur['nom']} "
            f"atteint la case "
            f"{TAILLE_PLATEAU} !\n\n"

            f"⭐ Score : "
            f"{joueur['points']}\n"

            f"🪙 Jetons : "
            f"{joueur['jetons']}\n"

            f"🏅 Niveau : "
            f"{niveau(joueur)}"
        )

        await query.edit_message_text(

            message,

            parse_mode="Markdown"
        )

        return


    type_carte = choisir_carte()


    # ========================================================
    # QUESTION OU DEFI
    # ========================================================

    if type_carte in [
        "QUESTION",
        "DEFI"
    ]:

        carte = core_tirer_carte(
            type_carte
        )

        joueur["carte"] = carte

        boutons = []

        for i, reponse in enumerate(
            carte["reponses"]
        ):

            boutons.append([

                InlineKeyboardButton(

                    f"{i + 1}. {reponse}",

                    callback_data=f"rep_{i}"
                )

            ])

        clavier_reponses = (
            InlineKeyboardMarkup(
                boutons
            )
        )

        if type_carte == "QUESTION":

            titre = (
                "🧠 *CARTE QUESTION*"
            )

        else:

            titre = (
                "⚡ *CARTE DÉFI*"
            )

        await query.edit_message_text(

            titre + "\n\n"

            f"{carte['question']}\n\n"

            "👇 Choisis ta réponse :",

            parse_mode="Markdown",

            reply_markup=clavier_reponses
        )

        return


    # ========================================================
    # CHANCE
    # ========================================================

    if type_carte == "CHANCE":

        carte = core_tirer_carte(
            "CHANCE"
        )

        action, valeur, texte = carte

        appliquer_effet(
            joueur,
            action,
            valeur
        )

        message += (

            "🍀 *CARTE CHANCE !*\n\n"

            f"{texte}\n\n"

            "━━━━━━━━━━━━━━\n"

            f"📍 Case : "
            f"{joueur['position']}/"
            f"{TAILLE_PLATEAU}\n"

            f"❤️ Vies : "
            f"{joueur['vies']}\n"

            f"⭐ Points : "
            f"{joueur['points']}\n"

            f"🪙 Jetons : "
            f"{joueur['jetons']}\n"

            f"🔥 Série : "
            f"{joueur['serie']}\n"
        )

        if verifier_victoire(joueur):

            ajouter_victoire(
                joueur["id"],
                joueur["points"],
                joueur["jetons"]
            )

            message += (

                "\n🏆 *VICTOIRE !*\n\n"

                "🍀 La Chance t'a permis "
                "d'atteindre la case 30 !"
            )

            await query.edit_message_text(

                message,

                parse_mode="Markdown"
            )

            return

        await query.edit_message_text(

            message,

            parse_mode="Markdown",

            reply_markup=clavier_jeu()
        )

        return


    # ========================================================
    # PIEGE
    # ========================================================

    if type_carte == "PIEGE":

        carte = core_tirer_carte(
            "PIEGE"
        )

        action, valeur, texte = carte

        appliquer_effet(
            joueur,
            action,
            valeur
        )

        message += (

            "🪤 *CARTE PIÈGE !*\n\n"

            f"{texte}\n\n"

            "━━━━━━━━━━━━━━\n"

            f"📍 Case : "
            f"{joueur['position']}/"
            f"{TAILLE_PLATEAU}\n"

            f"❤️ Vies : "
            f"{joueur['vies']}\n"

            f"⭐ Points : "
            f"{joueur['points']}\n"

            f"🪙 Jetons : "
            f"{joueur['jetons']}\n"

            f"🔥 Série : "
            f"{joueur['serie']}\n"
        )

        await query.edit_message_text(

            message,

            parse_mode="Markdown",

            reply_markup=clavier_jeu()
        )

        return


# ============================================================
# REPONSE TELEGRAM
# ============================================================

async def reponse(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    joueur = parties.get(
        user_id
    )

    if not joueur:

        await query.edit_message_text(
            "❌ Tu n'as pas de partie en cours."
        )

        return

    if "carte" not in joueur:

        await query.edit_message_text(
            "❌ Aucune question en cours."
        )

        return

    carte = joueur["carte"]

    try:

        choix = int(
            query.data.split("_")[1]
        )

    except (
        IndexError,
        ValueError
    ):

        await query.edit_message_text(
            "❌ Réponse invalide."
        )

        return

    resultat = traiter_reponse(
        joueur,
        carte,
        choix
    )

    message = ""


    if resultat["correct"]:

        message += (

            "✅ *BONNE RÉPONSE !*\n\n"

            f"⭐ +"
            f"{resultat['points_gagnes']}"
            f" points\n"

            "🪙 +1 jeton\n\n"
        )

        if resultat["bonus"] > 0:

            message += (

                "🔥 *SÉRIE DE 3 !*\n"

                "🎁 Bonus : +20 points\n"

                "🪙 Bonus : +1 jeton\n\n"
            )

        message += (

            f"💡 "
            f"{carte['explication']}\n\n"
        )

    else:

        bonne_reponse = (
            carte["reponses"][
                carte["bonne"]
            ]
        )

        message += (

            "❌ *MAUVAISE RÉPONSE !*\n\n"

            f"✅ Bonne réponse : "
            f"{bonne_reponse}\n\n"

            f"💡 "
            f"{carte['explication']}\n\n"

            "💔 Tu perds 1 vie.\n"

            f"❤️ Vies restantes : "
            f"{joueur['vies']}\n\n"
        )


    joueur.pop(
        "carte",
        None
    )


    # ========================================================
    # GAME OVER TELEGRAM
    # ========================================================

    if joueur["vies"] <= 0:

        enregistrer_score(
            joueur["id"],
            joueur["points"],
            joueur["jetons"]
        )

        message += (

            "💀 *GAME OVER !*\n\n"

            "Tu n'as plus de vies.\n\n"

            f"⭐ Score final : "
            f"{joueur['points']}\n"

            f"🪙 Jetons : "
            f"{joueur['jetons']}\n"

            f"🏅 Niveau : "
            f"{niveau(joueur)}"
        )

        clavier_reponse = (
            InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🔄 Rejouer",
                        callback_data="nouvelle_partie"
                    )
                ]

            ])
        )

    else:

        message += (

            "━━━━━━━━━━━━━━\n"

            f"📍 Case : "
            f"{joueur['position']}/"
            f"{TAILLE_PLATEAU}\n"

            f"❤️ Vies : "
            f"{joueur['vies']}\n"

            f"⭐ Points : "
            f"{joueur['points']}\n"

            f"🪙 Jetons : "
            f"{joueur['jetons']}\n"

            f"🔥 Série : "
            f"{joueur['serie']}\n"

            f"🏅 Niveau : "
            f"{niveau(joueur)}"
        )

        clavier_reponse = (
            InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🎲 Continuer",
                        callback_data="de"
                    )
                ],

                [
                    InlineKeyboardButton(
                        "📊 Profil",
                        callback_data="profil"
                    )
                ]

            ])
        )


    await query.edit_message_text(

        message,

        parse_mode="Markdown",

        reply_markup=clavier_reponse
    )


# ============================================================
# PROFIL
# ============================================================

async def profil(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    joueur = parties.get(
        query.from_user.id
    )

    if not joueur:

        await query.edit_message_text(

            "❌ Tu n'as pas encore "
            "commencé de partie.\n\n"

            "Utilise /jouer."
        )

        return

    clavier_profil = (
        InlineKeyboardMarkup([

            [
                InlineKeyboardButton(
                    "🎲 Retour au jeu",
                    callback_data="de"
                )
            ]

        ])
    )

    await query.edit_message_text(

        f"📊 *TON PROFIL*\n\n"
        f"{texte_joueur(joueur)}",

        parse_mode="Markdown",

        reply_markup=clavier_profil
    )


# ============================================================
# NOUVELLE PARTIE
# ============================================================

async def nouvelle_partie(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user = query.from_user

    nom = (
        user.first_name
        or "Joueur"
    )

    username = user.username

    enregistrer_joueur(
        user.id,
        username,
        nom
    )

    mettre_a_jour_joueur(
        user.id,
        username,
        nom
    )

    ajouter_partie(
        user.id
    )

    joueur = creer_joueur(
        user.id,
        nom,
        username
    )

    parties[user.id] = joueur

    await query.edit_message_text(

        "🎮 *NOUVELLE PARTIE !*\n\n"

        "📍 Case : 1/30\n"
        "❤️ Vies : 3\n"
        "⭐ Points : 0\n"
        "🪙 Jetons : 0\n\n"

        "🎯 Objectif : atteindre "
        "la case 30 !",

        parse_mode="Markdown",

        reply_markup=clavier_jeu()
    )


# ============================================================
# ABANDONNER
# ============================================================

async def stop(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    parties.pop(
        query.from_user.id,
        None
    )

    await query.edit_message_text(

        "🛑 *PARTIE ABANDONNÉE*\n\n"

        "Utilise /jouer pour recommencer.",

        parse_mode="Markdown"
    )


# ============================================================
# CLASSEMENT TELEGRAM
# ============================================================

async def afficher_classement(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    resultats = classement(
        10
    )

    texte = (
        "🏆 CLASSEMENT — TOP 10\n\n"
    )

    if not resultats:

        texte += (
            "Aucun joueur classé "
            "pour le moment."
        )

    else:

        for i, (
            username,
            nom,
            victoires,
            meilleur_score
        ) in enumerate(
            resultats,
            1
        ):

            pseudo = (

                f"@{username}"

                if username

                else nom
            )

            texte += (

                f"{i}. 👤 {pseudo}\n"

                f"   ⭐ Meilleur score : "
                f"{meilleur_score}\n"

                f"   🏆 Victoires : "
                f"{victoires}\n\n"
            )

    await query.edit_message_text(
        texte
    )


# ============================================================
# GESTION DES BOUTONS
# ============================================================

async def bouton(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    if query.data == "de":

        await lancer_de(
            update,
            context
        )

    elif query.data.startswith(
        "rep_"
    ):

        await reponse(
            update,
            context
        )

    elif query.data == "profil":

        await profil(
            update,
            context
        )

    elif query.data == "nouvelle_partie":

        await nouvelle_partie(
            update,
            context
        )

    elif query.data == "regles":

        await query.answer()

        await query.edit_message_text(

            "📜 *RÈGLES DE DÉFI RÉFLEXION*\n\n"

            "🎯 Atteins la case 30.\n\n"

            "🎲 Lance le dé à chaque tour.\n\n"

            "🧠 Réponds aux questions.\n\n"

            "⚡ Relève les défis.\n\n"

            "🍀 Chance : bonus de points "
            "ou déplacement.\n\n"

            "🪤 Piège : perte de points "
            "ou recul.\n\n"

            "❤️ Une mauvaise réponse "
            "fait perdre 1 vie.\n\n"

            "🔥 3 bonnes réponses "
            "consécutives donnent un bonus.\n\n"

            "🪙 Les bonnes réponses "
            "donnent des jetons.",

            parse_mode="Markdown"
        )

    elif query.data == "classement":

        await afficher_classement(
            update,
            context
        )

    elif query.data == "stop":

        await stop(
            update,
            context
        )


# ============================================================
# MAIN
# ============================================================

def main():

    if not TOKEN:

        print(
            "❌ TOKEN introuvable dans .env"
        )

        return

    creer_base()

    creer_table_utilisateurs_web()

    application = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "jouer",
            jouer
        )
    )

    application.add_handler(
        CommandHandler(
            "regles",
            regles
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            bouton
        )
    )

    print(
        "🤖 Bot démarré..."
    )

    print(
        "🎲 DÉFI RÉFLEXION est prêt !"
    )

    threading.Thread(
        target=lancer_serveur,
        daemon=True
    ).start()

    application.run_polling()


# ============================================================
# LANCEMENT
# ============================================================

if __name__ == "__main__":

    if os.getenv(
        "WEB_ONLY"
    ) == "1":

        lancer_serveur()

    else:

        main()