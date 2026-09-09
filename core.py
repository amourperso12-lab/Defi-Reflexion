import random

from questions import QUESTIONS, DEFIS


# ============================================================
# ⚙️ CONFIGURATION DU JEU
# ============================================================

TAILLE_PLATEAU = 30
VIES_DEPART = 3


# ============================================================
# 🍀 CHANCES
# ============================================================

CHANCES = [
    ("points", 20, "🍀 Tu gagnes 20 points !"),
    ("points", 30, "🍀 Super chance ! +30 points !"),
    ("points", 15, "🍀 Tu gagnes 15 points !"),
    ("avance", 2, "🍀 Chance ! Tu avances de 2 cases !"),
    ("avance", 3, "🍀 Grande chance ! Tu avances de 3 cases !"),
]


# ============================================================
# 🪤 PIÈGES
# ============================================================

PIEGES = [
    ("points", -10, "🪤 Tu perds 10 points !"),
    ("points", -15, "🪤 Tu perds 15 points !"),
    ("points", -20, "🪤 Tu perds 20 points !"),
    ("recule", 2, "🪤 Tu recules de 2 cases !"),
    ("recule", 3, "🪤 Tu recules de 3 cases !"),
]


# ============================================================
# 👤 CRÉER UN JOUEUR
# ============================================================

def creer_joueur(joueur_id, nom, username=None):

    return {
        "id": joueur_id,
        "nom": nom,
        "username": username,
        "position": 1,
        "points": 0,
        "vies": VIES_DEPART,
        "serie": 0,
        "jetons": 0,
    }


# ============================================================
# 🏅 CALCULER LE NIVEAU
# ============================================================

def niveau(joueur):

    points = joueur["points"]

    if points < 50:
        return "🥉 Débutant"

    elif points < 100:
        return "🥈 Intermédiaire"

    elif points < 150:
        return "🥇 Avancé"

    return "👑 Expert"


# ============================================================
# 🎲 LANCER LE DÉ
# ============================================================

def lancer_de(joueur):

    # 🎲 Génère un nombre aléatoire entre 1 et 6
    resultat = random.randint(1, 6)

    ancienne_position = joueur["position"]

    # 📍 Déplace le joueur
    joueur["position"] += resultat

    # 🚫 Ne jamais dépasser la case 30
    if joueur["position"] > TAILLE_PLATEAU:
        joueur["position"] = TAILLE_PLATEAU

    return {
        "de": resultat,
        "ancienne_position": ancienne_position,
        "nouvelle_position": joueur["position"],
        "victoire": joueur["position"] >= TAILLE_PLATEAU,
    }


# ============================================================
# 🃏 CHOISIR UNE CARTE
# ============================================================

def choisir_carte():
    """
    Choisit au hasard le type de carte à jouer.
    """

    return random.choice([
        "QUESTION",
        "DEFI",
        "CHANCE",
        "PIEGE"
    ])


# ============================================================
# 🃏 RÉCUPÉRER UNE CARTE
# ============================================================

def tirer_carte(type_carte):
    """
    Récupère une vraie carte selon son type.
    """

    # 🧠 Récupérer une question
    if type_carte == "QUESTION":
        return random.choice(QUESTIONS)

    # ⚡ Récupérer un défi
    if type_carte == "DEFI":
        return random.choice(DEFIS)

    # 🍀 Récupérer une chance
    if type_carte == "CHANCE":
        return random.choice(CHANCES)

    # 🪤 Récupérer un piège
    if type_carte == "PIEGE":
        return random.choice(PIEGES)

    # ❌ Type de carte inconnu
    return None


# ============================================================
# 🍀🪤 APPLIQUER UN EFFET
# ============================================================

def appliquer_effet(joueur, action, valeur):
    """
    Applique l'effet d'une carte Chance ou Piège au joueur.
    """

    # ⭐ Modifier les points
    if action == "points":

        joueur["points"] += valeur

        # Les points ne peuvent pas être négatifs
        if joueur["points"] < 0:
            joueur["points"] = 0

    # ➡️ Faire avancer le joueur
    elif action == "avance":

        joueur["position"] += valeur

        # 🚫 Ne jamais dépasser la case 30
        if joueur["position"] > TAILLE_PLATEAU:
            joueur["position"] = TAILLE_PLATEAU

    # ⬅️ Faire reculer le joueur
    elif action == "recule":

        joueur["position"] -= valeur

        # 🚫 Ne jamais descendre sous la case 1
        if joueur["position"] < 1:
            joueur["position"] = 1

    return joueur

# ============================================================
# 🧠 TRAITER UNE RÉPONSE
# ============================================================

def traiter_reponse(joueur, carte, reponse_index):
    """
    Traite la réponse d'un joueur à une question ou un défi.
    """

    bonne_reponse = carte["bonne"]

    # ✅ Bonne réponse
    if reponse_index == bonne_reponse:

        joueur["points"] += carte["points"]
        joueur["serie"] += 1
        joueur["jetons"] += 1

        bonus = 0

        # 🔥 3 bonnes réponses consécutives
        if joueur["serie"] >= 3:

            bonus = 20
            joueur["points"] += bonus
            joueur["jetons"] += 1
            joueur["serie"] = 0

        return {
            "correct": True,
            "points_gagnes": carte["points"],
            "bonus": bonus,
            "vies_perdues": 0,
            "serie": joueur["serie"],
            "jetons_gagnes": 1 + (1 if bonus > 0 else 0),
        }

    # ❌ Mauvaise réponse
    joueur["vies"] -= 1
    joueur["serie"] = 0

    return {
        "correct": False,
        "points_gagnes": 0,
        "bonus": 0,
        "vies_perdues": 1,
        "serie": 0,
        "jetons_gagnes": 0,
        
    }# ============================================================
# 🏆 VÉRIFIER LA VICTOIRE
# ============================================================

def verifier_victoire(joueur):
    """
    Vérifie si le joueur a atteint la case 30.
    """

    return joueur["position"] >= TAILLE_PLATEAU