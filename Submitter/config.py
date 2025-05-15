import os
import re

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# --- Configurazione CyberChallenge ---
# !! METTI I VALORI REALI !!
GAMESERVER_URL = "http://10.10.0.1:8080/flags"  # Usa POST ora
TEAM_TOKEN = "d98453257da6f0b806c894b0802d3983" # Usa il tuo token
FLAG_REGEX_STR = r"^[A-Z0-9]{31}=$" # Regex ufficiale
FLAG_REGEX = re.compile(FLAG_REGEX_STR)

# --- Configurazione Submitter ---
DATABASE_FILE = os.path.join(BASE_DIR, 'submitter_flags.db')
FLASK_SECRET_KEY = 'girolamo-trombetta' # Importante per Flask
# Intervallo minimo tra batch di invio (in secondi) - 60 sec / 30 req = 2 sec
SUBMISSION_INTERVAL_SECONDS = 2.0
SUBMISSION_BATCH_SIZE = 100 # Max flag per batch
REQUESTS_TIMEOUT = 10 # Timeout per richieste al game server
UI_FLAGS_PER_PAGE = 50 # Quante flag mostrare nella UI

# --- Stati Interni Usati nel DB e UI ---
STATUS_PENDING = "PENDING"
STATUS_ACCEPTED = "ACCEPTED"
STATUS_REJECTED = "REJECTED" # Copre duplicati, formato errato, own_flag
STATUS_OLD = "OLD"
STATUS_ERROR = "ERROR" # Errore invio, risposta server malformata, etc.
STATUS_INVALID = "INVALID" # Formato flag non valido all'input

# Mappa dagli status CyberChallenge ai nostri status interni
SERVER_STATUS_MAP = {
    "ACCEPTED": STATUS_ACCEPTED,
    "REJECTED": STATUS_REJECTED,
    "OWN_FLAG": STATUS_REJECTED, # Trattiamo come rejected
    "OLD": STATUS_OLD,
}
