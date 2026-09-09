import random
from questions import QUESTIONS, DEFIS


# ============================================================
# 🎲 DÉFI RÉFLEXION - VERSION 6
# ============================================================

TAILLE_PLATEAU = 30
VIES_DEPART = 3

#
# ============================================================
# 🍀 CHANCES
# ============================================================

CHANCES = [
    ("points", 20, "🍀 Tu gagnes 20 points !"),
    ("points", 30, "🍀 Super chance ! Tu gagnes 30 points !"),
    ("points", 15, "🍀 Tu gagnes 15 points !"),
    ("avance", 2, "🍀 Chance ! Tu avances de 2 cases !"),
    ("avance", 3, "🍀 Grande chance ! Tu avances de 3 cases !")
]


# ============================================================
# 🪤 PIÈGES
# ============================================================

PIEGES = [
    ("points", 10, "🪤 Tu perds 10 points !"),
    ("points", 15, "🪤 Tu perds 15 points !"),
    ("points", 20, "🪤 Tu perds 20 points !"),
    ("recule", 2, "🪤 Tu recules de 2 cases !"),
    ("recule", 3, "🪤 Tu recules de 3 cases !")
]


# ============================================================
# 🏅 CALCUL DU NIVEAU
# ============================================================

def niveau(joueur):
    points = joueur["points"]

    if points < 50:
        return "🥉 Débutant"
    elif points < 100:
        return "🥈 Intermédiaire"
    elif points < 150:
        return "🥇 Avancé"
    else:
        return "👑 Expert"


# ============================================================
# 🎲 AFFICHER LE PLATEAU
# ============================================================

def afficher_plateau(joueurs):
    print("\n" + "=" * 70)
    print("🎲 DÉFI RÉFLEXION - PLATEAU")
    print("=" * 70)

    for ligne in range(0, TAILLE_PLATEAU, 5):
        cases = []

        for case in range(ligne + 1, ligne + 6):
            symboles = ""

            for joueur in joueurs:
                if joueur["position"] == case:
                    symboles += joueur["symbole"]

            if symboles == "":
                symboles = "·"

            cases.append(f"{case:02d}[{symboles:^6}]")

        print("   ".join(cases))

    print("-" * 70)

    for joueur in joueurs:
        print(
            f'{joueur["symbole"]} {joueur["nom"]} | '
            f'Case: {joueur["position"]:02d} | '
            f'❤️ {joueur["vies"]} | '
            f'⭐ {joueur["points"]} pts | '
            f'🪙 {joueur["jetons"]} | '
            f'{niveau(joueur)}'
        )

    print("=" * 70)


# ============================================================
# 🧠 POSER UNE QUESTION
# ============================================================

def poser_question(carte, joueur):
    print("\n🧠 QUESTION")
    print("-" * 55)
    print(carte["question"])
    print()

    for i, reponse in enumerate(carte["reponses"], start=1):
        print(f"{i}. {reponse}")

    while True:
        choix = input("\n👉 Ta réponse (1-4) : ")

        if choix in ["1", "2", "3", "4"]:
            choix = int(choix) - 1
            break

        print("❌ Entre un nombre entre 1 et 4.")

    if choix == carte["bonne"]:
        print("\n✅ BRAVO ! Bonne réponse !")

        points = carte["points"]

        # 🔥 SÉRIE
        joueur["serie"] += 1

        if joueur["serie"] >= 3:
            print("🔥 SÉRIE DE 3 BONNES RÉPONSES !")
            print("🎁 BONUS : +20 points !")
            points += 20
            joueur["jetons"] += 1
            joueur["serie"] = 0

        joueur["points"] += points

        print(f"⭐ +{points} points")
        print(f'💡 {carte["explication"]}')

        # 🪙 Jeton
        joueur["jetons"] += 1
        print("🪙 Tu gagnes 1 jeton !")

        return True

    print("\n❌ MAUVAISE RÉPONSE !")

    joueur["serie"] = 0
    joueur["vies"] -= 1

    print(
        f'✅ La bonne réponse était : '
        f'{carte["reponses"][carte["bonne"]]}'
    )
    print(f'💡 {carte["explication"]}')
    print("💔 Tu perds 1 vie !")

    return False


# ============================================================
# 🧠 CARTE QUESTION
# ============================================================

def carte_question(joueur):
    carte = random.choice(QUESTIONS)
    return poser_question(carte, joueur)


# ============================================================
# ⚡ CARTE DÉFI
# ============================================================

def carte_defi(joueur):
    carte = random.choice(DEFIS)

    print("\n⚡ CARTE DÉFI !")

    return poser_question(carte, joueur)


# ============================================================
# 🍀 CARTE CHANCE
# ============================================================

def carte_chance(joueur):
    print("\n🍀 CARTE CHANCE !")

    action, valeur, message = random.choice(CHANCES)

    print(message)

    if action == "points":
        joueur["points"] += valeur

    elif action == "avance":
        joueur["position"] += valeur

        if joueur["position"] > TAILLE_PLATEAU:
            joueur["position"] = TAILLE_PLATEAU


# ============================================================
# 🪤 CARTE PIÈGE
# ============================================================

def carte_piege(joueur):
    print("\n🪤 CARTE PIÈGE !")

    action, valeur, message = random.choice(PIEGES)

    print(message)

    if action == "points":
        joueur["points"] -= valeur

        if joueur["points"] < 0:
            joueur["points"] = 0

    elif action == "recule":
        joueur["position"] -= valeur

        if joueur["position"] < 1:
            joueur["position"] = 1


# ============================================================
# 🃏 TIRER UNE CARTE
# ============================================================

def tirer_carte(joueur):
    cartes = [
        "QUESTION",
        "DEFI",
        "CHANCE",
        "PIEGE"
    ]

    carte = random.choice(cartes)

    print("\n" + "🃏" * 20)
    print(f"🎴 CARTE : {carte}")
    print("🃏" * 20)

    if carte == "QUESTION":
        carte_question(joueur)

    elif carte == "DEFI":
        carte_defi(joueur)

    elif carte == "CHANCE":
        carte_chance(joueur)

    elif carte == "PIEGE":
        carte_piege(joueur)


# ============================================================
# 🎲 LANCER LE DÉ
# ============================================================

def lancer_de(joueur):
    input(
        f'\n🎲 {joueur["nom"]}, '
        f'appuie sur ENTRÉE pour lancer le dé...'
    )

    resultat = random.randint(1, 6)

    print(f"🎲 Résultat du dé : {resultat}")

    joueur["position"] += resultat

    if joueur["position"] > TAILLE_PLATEAU:
        joueur["position"] = TAILLE_PLATEAU

    print(
        f'➡️ {joueur["nom"]} arrive à la case '
        f'{joueur["position"]}.'
    )


# ============================================================
# 👥 CRÉER LES JOUEURS
# ============================================================

def creer_joueurs():
    print("\n👥 CHOISIS LE NOMBRE DE JOUEURS")

    while True:
        choix = input("👉 Nombre de joueurs (2-4) : ")

        if choix in ["2", "3", "4"]:
            nombre = int(choix)
            break

        print("❌ Choisis 2, 3 ou 4.")

    symboles = ["🔵", "🔴", "🟢", "🟡"]

    joueurs = []

    for i in range(nombre):
        nom = input(
            f'{symboles[i]} Nom du joueur {i + 1} : '
        )

        if nom.strip() == "":
            nom = f"Joueur {i + 1}"

        joueurs.append({
            "nom": nom,
            "symbole": symboles[i],
            "position": 1,
            "points": 0,
            "vies": VIES_DEPART,
            "serie": 0,
            "jetons": 0
        })

    return joueurs


# ============================================================
# 🎮 JOUER
# ============================================================

def jouer():
    print("\n" + "=" * 70)
    print("🎲 DÉFI RÉFLEXION - VERSION 6")
    print("=" * 70)

    joueurs = creer_joueurs()

    tour = 0

    while True:

        # Retirer les joueurs qui n'ont plus de vies
        joueurs_actifs = [
            joueur for joueur in joueurs
            if joueur["vies"] > 0
        ]

        if len(joueurs_actifs) == 1 and len(joueurs) > 1:
            gagnant = joueurs_actifs[0]

            print("\n🏆 IL NE RESTE PLUS QU'UN JOUEUR !")
            print(f'🎉 {gagnant["nom"]} gagne !')
            break

        if len(joueurs_actifs) == 0:
            print("\n❌ Tous les joueurs ont perdu leurs vies.")
            print("🎮 Partie terminée.")
            break

        # Trouver le prochain joueur actif
        compteur = 0

        while joueurs[tour]["vies"] <= 0:
            tour += 1

            if tour >= len(joueurs):
                tour = 0

            compteur += 1

            if compteur > len(joueurs):
                break

        joueur = joueurs[tour]

        afficher_plateau(joueurs)

        print(
            f'\n🎯 TOUR DE {joueur["symbole"]} '
            f'{joueur["nom"]}'
        )
        print(
            f'❤️ Vies : {joueur["vies"]} | '
            f'⭐ Points : {joueur["points"]} | '
            f'🪙 Jetons : {joueur["jetons"]}'
        )

        lancer_de(joueur)

        # Victoire immédiate
        if joueur["position"] >= TAILLE_PLATEAU:
            afficher_plateau(joueurs)

            print("\n" + "🏆" * 20)
            print("🎉 VICTOIRE !")
            print(f'🏆 {joueur["nom"]} a gagné !')
            print(f'⭐ Score : {joueur["points"]} points')
            print(f'🪙 Jetons : {joueur["jetons"]}')
            print(f'🏅 Niveau : {niveau(joueur)}')
            print("🏆" * 20)

            break

        # Tirer une carte
        tirer_carte(joueur)

        # Vérifier les vies
        if joueur["vies"] <= 0:
            print(
                f'\n💀 {joueur["nom"]} a perdu toutes ses vies !'
            )

        # Vérifier si une carte a fait atteindre la case 30
        if joueur["position"] >= TAILLE_PLATEAU:
            afficher_plateau(joueurs)

            print("\n🏆 CARTE DÉCISIVE !")
            print(
                f'🎉 {joueur["nom"]} atteint la case 30 '
                f'et gagne !'
            )
            print(f'⭐ Score : {joueur["points"]} points')
            print(f'🏅 Niveau : {niveau(joueur)}')

            break

        # Joueur suivant
        tour += 1

        if tour >= len(joueurs):
            tour = 0

    print("\n🎮 FIN DE LA PARTIE")

    # Classement final
    print("\n🏆 CLASSEMENT FINAL")
    print("-" * 60)

    classement = sorted(
        joueurs,
        key=lambda joueur: joueur["points"],
        reverse=True
    )

    for i, joueur in enumerate(classement, start=1):
        print(
            f'{i}. {joueur["symbole"]} {joueur["nom"]} '
            f'| ⭐ {joueur["points"]} pts '
            f'| 🪙 {joueur["jetons"]} '
            f'| {niveau(joueur)}'
        )

    input("\n👉 Appuie sur ENTRÉE pour revenir au menu...")


# ============================================================
# 📜 RÈGLES
# ============================================================

def afficher_regles():
    print("\n" + "=" * 70)
    print("📜 RÈGLES DU JEU")
    print("=" * 70)

    print("""
🎯 OBJECTIF
Être le premier joueur à atteindre la case 30.

🎲 LE DÉ
À chaque tour, le joueur lance un dé de 1 à 6.

🧠 CARTE QUESTION
Réponds à une question éducative.
Une bonne réponse rapporte des points.

⚡ CARTE DÉFI
Résous un petit problème de logique ou de réflexion.

🍀 CARTE CHANCE
Tu peux gagner des points ou avancer.

🪤 CARTE PIÈGE
Tu peux perdre des points ou reculer.

❤️ VIES
Chaque joueur commence avec 3 vies.
Une mauvaise réponse fait perdre 1 vie.

🔥 SÉRIE
3 bonnes réponses consécutives donnent un bonus de 20 points
et 1 jeton.

🪙 JETONS
Les jetons récompensent les bonnes réponses et les séries.

🏅 NIVEAUX
🥉 Débutant
🥈 Intermédiaire
🥇 Avancé
👑 Expert
""")

    input("\n👉 Appuie sur ENTRÉE pour revenir au menu...")


# ============================================================
# 📋 MENU
# ============================================================

def menu():
    while True:
        print("\n")
        print("=" * 70)
        print("🎲 DÉFI RÉFLEXION")
        print("=" * 70)
        print("1️⃣  Jouer")
        print("2️⃣  Règles")
        print("3️⃣  Quitter")
        print("=" * 70)

        choix = input("👉 Choisis une option : ")

        if choix == "1":
            jouer()

        elif choix == "2":
            afficher_regles()

        elif choix == "3":
            print("\n👋 Merci d'avoir joué à DÉFI RÉFLEXION !")
            break

        else:
            print("❌ Choix incorrect.")


# ============================================================
# 🚀 DÉMARRAGE
# ============================================================

if __name__ == "__main__":
    menu()