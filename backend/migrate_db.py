"""
Script de migration temporaire pour mettre à jour la table 'users'.
Modifie la colonne 'email' pour supporter le chiffrement et ajoute la colonne 'phone'.
"""
import os
import psycopg2
from config import Config


def run_migration():
    # 1. Récupération de l'URL de connexion PostgreSQL (depuis la config ou l'environnement)
    db_url = os.environ.get('DATABASE_URL') or getattr(Config, 'SQLALCHEMY_DATABASE_URI', None)

    if not db_url:
        print("❌ Erreur : Impossible de trouver l'URL de la base de données (DATABASE_URL).")
        return

    print("🔄 Connexion à la base de données PostgreSQL de Render...")
    try:
        # Connexion directe via le driver PostgreSQL
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        print("🛠️ Exécution des modifications SQL...")

        # Requête 1 : Changer le type de 'email' en TEXT pour stocker de longues chaînes chiffrées
        cursor.execute("ALTER TABLE users ALTER COLUMN email TYPE TEXT;")

        # Requête 2 : Autoriser la colonne 'email' à être vide (nullable) pour l'admin initial
        cursor.execute("ALTER TABLE users ALTER COLUMN email DROP NOT NULL;")

        # Requête 3 : Supprimer l'ancienne contrainte d'unicité sur l'e-mail pour éviter les conflits d'index chiffrés
        # Note : PostgreSQL nomme souvent cet index 'uq_users_email' ou 'users_email_key'
        try:
            cursor.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key;")
            cursor.execute("DROP INDEX IF EXISTS index_users_on_email;")
        except Exception as index_err:
            print(f"⚠️ Note sur l'index (peut être ignorée) : {index_err}")
            conn.rollback()  # Annule uniquement l'erreur d'index si elle n'existe pas

        # Requête 4 : Ajouter la colonne 'phone' de type TEXT si elle n'existe pas déjà
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT;")

        # Validation des changements
        conn.commit()
        print("✅ Base de données PostgreSQL mise à jour avec succès sans perte de données !")

    except Exception as e:
        print(f"❌ Échec de la migration SQL : {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()


if __name__ == '__main__':
    run_migration()
