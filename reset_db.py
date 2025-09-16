import psycopg2
import os

# Uses settings from EventManagment/settings.py
DB_NAME = os.getenv("PG_DB_NAME", "EventManagement")
DB_USER = os.getenv("PG_DB_USER", "farhana")
DB_PASSWORD = os.getenv("PG_DB_PASSWORD", "1234")
DB_HOST = os.getenv("PG_DB_HOST", "localhost")
DB_PORT = int(os.getenv("PG_DB_PORT", "5432"))


def reset_database():
    # Connect to the default 'postgres' database to manage DBs
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Terminate existing connections to the target database
    cur.execute(
        """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = %s AND pid <> pg_backend_pid();
        """,
        (DB_NAME,),
    )

    # Drop and recreate the database
    cur.execute(f"DROP DATABASE IF EXISTS \"{DB_NAME}\";")
    cur.execute(f"CREATE DATABASE \"{DB_NAME}\" WITH OWNER = \"{DB_USER}\" ENCODING 'UTF8';")

    cur.close()
    conn.close()


if __name__ == "__main__":
    reset_database()
    print(f"Database '{DB_NAME}' has been reset successfully.")


