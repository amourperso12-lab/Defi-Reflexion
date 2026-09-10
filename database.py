import sqlite3
from datetime import datetime


DATABASE = "joueurs.db"


# ============================================================
# 🔌 CONNEXION
# ============================================================

def connexion_base():
    return sqlite3.connect(DATABASE)


# ============================================================
# 🗄️ CRÉER LA BASE
# ============================================================

def creer_base():

    connexion = connexion_base()
    curseur = connexion.cursor()

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS joueurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            nom TEXT NOT NULL,
            date_inscription TEXT NOT NULL,
            parties INTEGER DEFAULT 0,
            victoires INTEGER DEFAULT 0,
            score_total INTEGER DEFAULT 0,
            meilleur_score INTEGER DEFAULT 0,
            jetons INTEGER DEFAULT 0
        )
    """)

    connexion.commit()
    connexion.close()


# ============================================================
# 👤 ENREGISTRER / METTRE À JOUR UN JOUEUR
# ============================================================

def enregistrer_joueur(telegram_id, username, nom):

    connexion = connexion_base()
    curseur = connexion.cursor()

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    curseur.execute("""
        INSERT OR IGNORE INTO joueurs
        (telegram_id, username, nom, date_inscription)
        VALUES (?, ?, ?, ?)
    """, (telegram_id, username, nom, date))

    connexion.commit()
    connexion.close()


def mettre_a_jour_joueur(telegram_id, username, nom):

    connexion = connexion_base()
    curseur = connexion.cursor()

    curseur.execute("""
        UPDATE joueurs
        SET username = ?, nom = ?
        WHERE telegram_id = ?
    """, (username, nom, telegram_id))

    connexion.commit()
    connexion.close()


# ============================================================
# 🎮 AJOUTER UNE PARTIE
# ============================================================

def ajouter_partie(telegram_id):

    connexion = connexion_base()
    curseur = connexion.cursor()

    curseur.execute("""
        UPDATE joueurs
        SET parties = parties + 1
        WHERE telegram_id = ?
    """, (telegram_id,))

    connexion.commit()
    connexion.close()


# ============================================================
# 🏆 ENREGISTRER UNE VICTOIRE
# ============================================================

def ajouter_victoire(telegram_id, score, jetons):

    connexion = connexion_base()
    curseur = connexion.cursor()

    curseur.execute("""
        UPDATE joueurs
        SET
            victoires = victoires + 1,
            score_total = score_total + ?,
            meilleur_score = CASE
                WHEN ? > meilleur_score THEN ?
                ELSE meilleur_score
            END,
            jetons = jetons + ?
        WHERE telegram_id = ?
    """, (
        score,
        score,
        score,
        jetons,
        telegram_id
    ))
    connexion.commit()
    connexion.close()

# ============================================================
# 💾 ENREGISTRER LE SCORE D'UNE PARTIE TERMINÉE
# ============================================================

def enregistrer_score(telegram_id, score, jetons):

    connexion = connexion_base()
    curseur = connexion.cursor()

    curseur.execute("""
        UPDATE joueurs
        SET
            score_total = score_total + ?,
            meilleur_score = CASE
                WHEN ? > meilleur_score THEN ?
                ELSE meilleur_score
            END,
            jetons = jetons + ?
        WHERE telegram_id = ?
    """, (
        score,
        score,
        score,
        jetons,
        telegram_id
    ))

    connexion.commit()
    connexion.close()


# ============================================================
# 📊 RÉCUPÉRER LE PROFIL
# ============================================================

def obtenir_joueur(telegram_id):

    connexion = connexion_base()
    curseur = connexion.cursor()

    curseur.execute("""
        SELECT
            telegram_id,
            username,
            nom,
            parties,
            victoires,
            score_total,
            meilleur_score,
            jetons
        FROM joueurs
        WHERE telegram_id = ?
    """, (telegram_id,))

    resultat = curseur.fetchone()

    connexion.close()

    return resultat


# ============================================================
# 🏆 CLASSEMENT
# ============================================================

def classement(limite=10):

    connexion = connexion_base()
    curseur = connexion.cursor()

    curseur.execute("""
        SELECT
            username,
            nom,
            victoires,
            meilleur_score
        FROM joueurs
        ORDER BY meilleur_score DESC, victoires DESC
        LIMIT ?
    """, (limite,))

    resultats = curseur.fetchall()

    connexion.close()

    return resultats
def creer_table_utilisateurs_web():
    connexion = connexion_base()
    curseur = connexion.cursor()

    curseur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs_web (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            date_inscription TEXT NOT NULL
        )
    """)

    connexion.commit()
    connexion.close()


def creer_utilisateur_web(username, password_hash):
    connexion = connexion_base()
    curseur = connexion.cursor()

    try:
        curseur.execute("""
            INSERT INTO utilisateurs_web
            (username, password_hash, date_inscription)
            VALUES (?, ?, ?)
        """, (
            username,
            password_hash,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        connexion.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connexion.close()


def obtenir_utilisateur_web(username):
    connexion = connexion_base()
    curseur = connexion.cursor()

    curseur.execute("""
        SELECT id, username, password_hash
        FROM utilisateurs_web
        WHERE username = ?
    """, (username,))

    resultat = curseur.fetchone()

    connexion.close()

    return resultat

def enregistrer_joueur_web(web_id, username):
    connexion = connexion_base()
    curseur = connexion.cursor()

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    curseur.execute("""
        INSERT OR IGNORE INTO joueurs
        (telegram_id, username, nom, date_inscription)
        VALUES (?, ?, ?, ?)
    """, (
        web_id,
        username,
        username,
        date
    ))

    connexion.commit()
    connexion.close()