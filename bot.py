import os
import random
import threading

from dotenv import load_dotenv

from flask import Flask, render_template
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
)


# ============================================================
# CONFIGURATION
# ============================================================

TOKEN = os.getenv("TELEGRAM_TOKEN")

TAILLE_PLATEAU = 30

app = Flask(__name__)


@app.route("/")
def accueil():
    return render_template("index.html")

def lancer_serveur():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ============================================================
# PARTIES EN COURS
# ============================================================

parties = {}


# ============================================================
# AFFICHER LE JOUEUR
# ============================================================

def texte_joueur(joueur):

    username = joueur.get("username")

    if username:
        identifiant = f"@{username}"
    else:
        identifiant = "Aucun username"

    return (
        f"👤 {joueur['nom']}\n"
        f"🔹 {identifiant}\n\n"
        f"📍 Case : {joueur['position']}/{TAILLE_PLATEAU}\n"
        f"❤️ Vies : {joueur['vies']}\n"
        f"⭐ Points : {joueur['points']}\n"
        f"🪙 Jetons : {joueur['jetons']}\n"
        f"🔥 Série : {joueur['serie']}\n"
        f"🏅 Niveau : {niveau(joueur)}"
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
# START
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

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
# JOUER
# ============================================================

async def jouer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    nom = user.first_name or "Joueur"
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

    ajouter_partie(user.id)

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
# RÈGLES
# ============================================================

async def regles(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📜 *RÈGLES DE DÉFI RÉFLEXION*\n\n"
        "🎯 Atteins la case 30.\n\n"
        "🎲 Lance le dé à chaque tour.\n\n"
        "🧠 Réponds aux questions.\n\n"
        "⚡ Relève les défis.\n\n"
        "🍀 Chance : bonus de points ou déplacement.\n\n"
        "🪤 Piège : perte de points ou recul.\n\n"
        "❤️ Une mauvaise réponse fait perdre 1 vie.\n\n"
        "🔥 3 bonnes réponses consécutives donnent un bonus.\n\n"
        "🪙 Les bonnes réponses donnent des jetons.",
        parse_mode="Markdown"
    )


# ============================================================
# LANCER LE DÉ
# ============================================================

async def lancer_de(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in parties:

        await query.edit_message_text(
            "❌ Tu n'as pas de partie en cours.\n\n"
            "Utilise /jouer pour commencer."
        )
        return

    joueur = parties[user_id]

    # Utiliser le cerveau du jeu
    resultat = core_lancer_de(joueur)

    de = resultat["de"]
    ancienne_position = resultat["ancienne_position"]
    nouvelle_position = resultat["nouvelle_position"]

    message = (
        "🎲 *LANCER DU DÉ*\n\n"
        f"🎲 Résultat : *{de}*\n\n"
        f"📍 Case : {ancienne_position} ➡️ "
        f"*{nouvelle_position}*\n\n"
    )

    # Vérifier la victoire
    if verifier_victoire(joueur):

        ajouter_victoire(
            joueur["id"],
            joueur["points"],
            joueur["jetons"]
        )

        message += (
            "🏆 *VICTOIRE !* 🏆\n\n"
            f"🎉 {joueur['nom']} atteint la case "
            f"{TAILLE_PLATEAU} !\n\n"
            f"⭐ Score : {joueur['points']}\n"
            f"🪙 Jetons : {joueur['jetons']}\n"
            f"🏅 Niveau : {niveau(joueur)}"
        )

        await query.edit_message_text(
            message,
            parse_mode="Markdown"
        )

        return

    # Choisir une carte
    type_carte = choisir_carte()

    # ========================================================
    # QUESTION OU DÉFI
    # ========================================================

    if type_carte in ["QUESTION", "DEFI"]:

        carte = core_tirer_carte(type_carte)

        joueur["carte"] = carte

        boutons = []

        for i, reponse in enumerate(carte["reponses"]):

            boutons.append([
                InlineKeyboardButton(
                    f"{i + 1}. {reponse}",
                    callback_data=f"rep_{i}"
                )
            ])

        clavier = InlineKeyboardMarkup(boutons)

        if type_carte == "QUESTION":
            titre = "🧠 *CARTE QUESTION*"
        else:
            titre = "⚡ *CARTE DÉFI*"

        await query.edit_message_text(
            titre + "\n\n"
            f"{carte['question']}\n\n"
            "👇 Choisis ta réponse :",
            parse_mode="Markdown",
            reply_markup=clavier
        )

        return

    # ========================================================
    # CHANCE
    # ========================================================

    if type_carte == "CHANCE":

        carte = core_tirer_carte("CHANCE")

        action, valeur, texte = carte

        # Appliquer l'effet avec core.py
        appliquer_effet(
            joueur,
            action,
            valeur
        )

        message += (
            "🍀 *CARTE CHANCE !*\n\n"
            f"{texte}\n\n"
            "━━━━━━━━━━━━━━\n"
            f"📍 Case : {joueur['position']}/{TAILLE_PLATEAU}\n"
            f"❤️ Vies : {joueur['vies']}\n"
            f"⭐ Points : {joueur['points']}\n"
            f"🪙 Jetons : {joueur['jetons']}\n"
            f"🔥 Série : {joueur['serie']}\n"
        )

        # Vérifier si la Chance a amené le joueur à la case 30
        if verifier_victoire(joueur):

            ajouter_victoire(
                joueur["id"],
                joueur["points"],
                joueur["jetons"]
            )

            message += (
                "\n🏆 *VICTOIRE !*\n\n"
                "🍀 La Chance t'a permis d'atteindre "
                "la case 30 !"
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
    # PIÈGE
    # ========================================================

    if type_carte == "PIEGE":

        carte = core_tirer_carte("PIEGE")

        action, valeur, texte = carte

        # Appliquer l'effet avec core.py
        appliquer_effet(
            joueur,
            action,
            valeur
        )

        message += (
            "🪤 *CARTE PIÈGE !*\n\n"
            f"{texte}\n\n"
            "━━━━━━━━━━━━━━\n"
            f"📍 Case : {joueur['position']}/{TAILLE_PLATEAU}\n"
            f"❤️ Vies : {joueur['vies']}\n"
            f"⭐ Points : {joueur['points']}\n"
            f"🪙 Jetons : {joueur['jetons']}\n"
            f"🔥 Série : {joueur['serie']}\n"
        )

        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=clavier_jeu()
        )

        return


# ============================================================
# RÉPONSE
# ============================================================

async def reponse(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    joueur = parties.get(user_id)

    if not joueur:
        return

    if "carte" not in joueur:

        await query.edit_message_text(
            "❌ Aucune question en cours."
        )
        return

    carte = joueur["carte"]

    choix = int(query.data.split("_")[1])

    # Utiliser le cerveau du jeu
    resultat = traiter_reponse(
        joueur,
        carte,
        choix
    )

    message = ""

    # Bonne réponse
    if resultat["correct"]:

        message += (
            "✅ *BONNE RÉPONSE !*\n\n"
            f"⭐ +{resultat['points_gagnes']} points\n"
            "🪙 +1 jeton\n\n"
        )

        if resultat["bonus"] > 0:

            message += (
                "🔥 *SÉRIE DE 3 !*\n"
                "🎁 Bonus : +20 points\n"
                "🪙 Bonus : +1 jeton\n\n"
            )

        message += (
            f"💡 {carte['explication']}\n\n"
        )

    # Mauvaise réponse
    else:

        bonne_reponse = carte["reponses"][carte["bonne"]]

        message += (
            "❌ *MAUVAISE RÉPONSE !*\n\n"
            f"✅ Bonne réponse : {bonne_reponse}\n\n"
            f"💡 {carte['explication']}\n\n"
            "💔 Tu perds 1 vie.\n"
            f"❤️ Vies restantes : {joueur['vies']}\n\n"
        )

    joueur.pop("carte", None)

    # Game Over

    if joueur["vies"] <= 0:

        enregistrer_score(
            joueur["id"],
            joueur["points"],
            joueur["jetons"]
        )

        message += (
            "💀 *GAME OVER !*\n\n"
            "Tu n'as plus de vies.\n\n"
            f"⭐ Score final : {joueur['points']}\n"
            f"🪙 Jetons : {joueur['jetons']}\n"
            f"🏅 Niveau : {niveau(joueur)}"
        )

        clavier = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔄 Rejouer",
                    callback_data="nouvelle_partie"
                )
            ]
        ])

    else:

        message += (
            "━━━━━━━━━━━━━━\n"
            f"📍 Case : {joueur['position']}/{TAILLE_PLATEAU}\n"
            f"❤️ Vies : {joueur['vies']}\n"
            f"⭐ Points : {joueur['points']}\n"
            f"🪙 Jetons : {joueur['jetons']}\n"
            f"🔥 Série : {joueur['serie']}\n"
            f"🏅 Niveau : {niveau(joueur)}"
        )

        clavier = InlineKeyboardMarkup([
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

    await query.edit_message_text(
        message,
        parse_mode="Markdown",
        reply_markup=clavier
    )


# ============================================================
# PROFIL
# ============================================================

async def profil(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    joueur = parties.get(query.from_user.id)

    if not joueur:

        await query.edit_message_text(
            "❌ Tu n'as pas encore commencé de partie.\n\n"
            "Utilise /jouer."
        )
        return

    clavier = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎲 Retour au jeu",
                callback_data="de"
            )
        ]
    ])

    await query.edit_message_text(
        f"📊 *TON PROFIL*\n\n{texte_joueur(joueur)}",
        parse_mode="Markdown",
        reply_markup=clavier
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

    nom = user.first_name or "Joueur"
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

    ajouter_partie(user.id)

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
        "🎯 Objectif : atteindre la case 30 !",
        parse_mode="Markdown",
        reply_markup=clavier_jeu()
    )


# ============================================================
# ABANDONNER
# ============================================================

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    parties.pop(query.from_user.id, None)

    await query.edit_message_text(
        "🛑 *PARTIE ABANDONNÉE*\n\n"
        "Utilise /jouer pour recommencer.",
        parse_mode="Markdown"
    )


# ============================================================
# GESTION DES BOUTONS
# ============================================================

async def afficher_classement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    resultats = classement(10)

    texte = "🏆 CLASSEMENT — TOP 10\n\n"

    if not resultats:
        texte += "Aucun joueur classé pour le moment."
    else:
        for i, (username, nom, victoires, meilleur_score) in enumerate(resultats, 1):
            pseudo = f"@{username}" if username else nom

            texte += (
                f"{i}. 👤 {pseudo}\n"
                f"   ⭐ Meilleur score : {meilleur_score}\n"
                f"   🏆 Victoires : {victoires}\n\n"
            )

    await query.edit_message_text(texte)


async def bouton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.data == "de":
        await lancer_de(update, context)

    elif query.data.startswith("rep_"):
        await reponse(update, context)

    elif query.data == "profil":
        await profil(update, context)

    elif query.data == "nouvelle_partie":
        await nouvelle_partie(update, context)

    elif query.data == "regles":
        await query.answer()
        await query.edit_message_text(
            "📜 *RÈGLES DE DÉFI RÉFLEXION*\n\n"
            "🎯 Atteins la case 30.\n\n"
            "🎲 Lance le dé à chaque tour.\n\n"
            "🧠 Réponds aux questions.\n\n"
            "⚡ Relève les défis.\n\n"
            "🍀 Chance : bonus de points ou déplacement.\n\n"
            "🪤 Piège : perte de points ou recul.\n\n"
            "❤️ Une mauvaise réponse fait perdre 1 vie.\n\n"
            "🔥 3 bonnes réponses consécutives donnent un bonus.\n\n"
            "🪙 Les bonnes réponses donnent des jetons.",
            parse_mode="Markdown"
        )

    elif query.data == "classement":
        await afficher_classement(update, context)

    elif query.data == "stop":
        await stop(update, context)

# ============================================================
# MAIN
# ============================================================

def main():

    if not TOKEN:
        print("❌ TOKEN introuvable dans .env")
        return

    creer_base()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("jouer", jouer)
    )

    application.add_handler(
        CommandHandler("regles", regles)
    )

    application.add_handler(
        CallbackQueryHandler(bouton)
    )

    print("🤖 Bot démarré...")
    print("🎲 DÉFI RÉFLEXION est prêt !")

    threading.Thread(
        target=lancer_serveur,
        daemon=True
    ).start()

    application.run_polling()


if __name__ == "__main__":
    main()