import sqlite3
import datetime
from flask import g
from config import DATABASE_FILE, STATUS_PENDING, STATUS_INVALID

DATABASE = DATABASE_FILE

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        db.row_factory = sqlite3.Row
    return db

def close_connection(exception=None): # Aggiunto exception=None per teardown
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # Tabella migliorata per contenere più info
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flag TEXT UNIQUE NOT NULL,
                author TEXT DEFAULT 'unknown',
                service TEXT DEFAULT 'unknown',
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                submitted_at TIMESTAMP NULL,
                status TEXT NOT NULL,
                server_response TEXT NULL,
                inferred_round INTEGER NULL,
                inferred_team INTEGER NULL,
                inferred_service INTEGER NULL
            )
        ''')
        # Indici per velocizzare i filtri
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_flags_status ON flags (status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_flags_author ON flags (author)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_flags_service ON flags (service)')
        db.commit()
    print("Database initialized.")

def add_flag(flag, author, service, status=STATUS_PENDING, inferred_info=None):
    """Aggiunge una flag al DB. Ritorna l'ID se aggiunta/esistente, None in caso di errore grave."""
    db = get_db()
    inferred = inferred_info or {}
    try:
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO flags (flag, author, service, status,
                               inferred_round, inferred_team, inferred_service)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (flag, author, service, status,
             inferred.get('round'), inferred.get('team'), inferred.get('service'))
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Flag già presente, potremmo voler restituire l'ID esistente
        cursor.execute("SELECT id FROM flags WHERE flag = ?", (flag,))
        existing = cursor.fetchone()
        return existing['id'] if existing else None # Ritorna ID esistente
    except Exception as e:
        print(f"Errore DB in add_flag: {e}")
        db.rollback()
        return None

def get_flags_by_status(status, limit=100):
    """Recupera flag con un certo stato."""
    cursor = get_db().cursor()
    cursor.execute("SELECT id, flag FROM flags WHERE status = ? ORDER BY received_at ASC LIMIT ?", (status, limit))
    return cursor.fetchall()

def update_flag_status(flag_id, new_status, server_response=""):
    """Aggiorna stato, timestamp invio e risposta server."""
    db = get_db()
    now = datetime.datetime.now()
    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE flags SET status = ?, submitted_at = ?, server_response = ? WHERE id = ?",
            (new_status, now, server_response, flag_id)
        )
        db.commit()
        return True
    except Exception as e:
        print(f"Errore DB in update_flag_status per ID {flag_id}: {e}")
        db.rollback()
        return False

def get_filtered_flags(author=None, service=None, status=None, limit=100):
    """Recupera flag filtrate per la UI."""
    query = "SELECT * FROM flags"
    conditions = []
    params = []

    if author:
        conditions.append("author LIKE ?")
        params.append(f"%{author}%")
    if service:
        conditions.append("service LIKE ?")
        params.append(f"%{service}%")
    if status:
        conditions.append("status = ?")
        params.append(status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY received_at DESC LIMIT ?"
    params.append(limit)

    cursor = get_db().cursor()
    cursor.execute(query, params)
    return cursor.fetchall()

def get_stats():
    """ Ottiene statistiche veloci per la UI """
    stats = {}
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT status, COUNT(*) as count FROM flags GROUP BY status")
        for row in cursor.fetchall():
            stats[row['status']] = row['count']
        cursor.execute("SELECT COUNT(*) as total FROM flags")
        stats['TOTAL'] = cursor.fetchone()['total']
    except Exception as e:
        print(f"Errore DB in get_stats: {e}")
    return stats

def delete_flag(flag_id):
    """Elimina una singola flag dal database usando il suo ID."""
    db = get_db()
    try:
        cursor = db.cursor()
        cursor.execute("DELETE FROM flags WHERE id = ?", (flag_id,))
        db.commit()
        # Restituisce il numero di righe eliminate (dovrebbe essere 1 o 0)
        return cursor.rowcount
    except Exception as e:
        print(f"Errore DB in delete_flag per ID {flag_id}: {e}")
        db.rollback()
        return 0
