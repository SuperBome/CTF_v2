import time
import threading
import logging # Importa logging standard
from flask import Flask, request, jsonify, render_template, g, redirect, url_for
from config import (
    FLASK_SECRET_KEY, SUBMISSION_INTERVAL_SECONDS, SUBMISSION_BATCH_SIZE,
    UI_FLAGS_PER_PAGE, # Valori di configurazione generale
    # Assicurati che TUTTI gli stati usati in app.py siano qui:
    STATUS_PENDING, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_OLD,
    STATUS_ERROR, STATUS_INVALID
)
import database
import submitter
from flask import render_template_string

# Configura logging di base
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

# --- Gestione Database nel contesto Flask ---
@app.before_request
def before_request():
    g.db = database.get_db()

@app.teardown_appcontext
def teardown_db(exception=None):
    database.close_connection(exception)

# --- Background Submitter Thread ---
submitter_thread_stop_event = threading.Event()

def submission_worker():
    """Ciclo del worker che invia flag."""
    print("Submission worker started.")
    last_run = 0
    while not submitter_thread_stop_event.is_set():
        now = time.time()
        if now - last_run >= SUBMISSION_INTERVAL_SECONDS:
            last_run = now
            try:
                # Esegui il ciclo dentro il contesto dell'app per accedere a g.db
                with app.app_context():
                    run_submission_cycle()
            except Exception as e:
                logging.error(f"Errore nel ciclo di invio: {e}", exc_info=True)

        # Attendi un po' prima di ricontrollare, o fino allo stop
        submitter_thread_stop_event.wait(max(0, SUBMISSION_INTERVAL_SECONDS - (time.time() - last_run)))
    print("Submission worker stopped.")


def run_submission_cycle():
    """Prende flag PENDING, le invia, aggiorna il DB."""
    pending_flags_records = database.get_flags_by_status(STATUS_PENDING, limit=SUBMISSION_BATCH_SIZE)

    if not pending_flags_records:
        # logging.debug("Nessuna flag PENDING trovata.")
        return

    flags_to_submit_dict = {record['id']: record['flag'] for record in pending_flags_records}
    flag_strings_batch = list(flags_to_submit_dict.values())

    results = submitter.submit_flags_batch(flag_strings_batch) # Invia il batch

    # Aggiorna il DB con i risultati
    processed_count = 0
    for flag_id, original_flag_str in flags_to_submit_dict.items():
        if original_flag_str in results:
            status, response_msg = results[original_flag_str]
            database.update_flag_status(flag_id, status, response_msg)
            processed_count += 1
        else:
            # Questo non dovrebbe succedere se submit_flags_batch funziona correttamente
             logging.warning(f"Flag ID {flag_id} ({original_flag_str}) non trovata nei risultati dell'invio.")
             # Potresti marcarla come ERROR qui per investigare
             # database.update_flag_status(flag_id, STATUS_ERROR, "Flag missing from batch results")

    logging.info(f"Ciclo di invio completato. Processate {processed_count}/{len(flag_strings_batch)} flag PENDING.")


# --- Route API ---
@app.route('/api/submit', methods=['POST'])
def api_add_flag():
    """Endpoint per ricevere flag dagli script di exploit."""
    if request.is_json:
        data = request.get_json()
        flag = data.get('flag')
        author = data.get('author', 'json_api')
        service = data.get('service', 'unknown_service')
    else: # Supporta anche form data
        flag = request.form.get('flag')
        author = request.form.get('author', 'form_api')
        service = request.form.get('service', 'unknown_service')

    if not flag:
        return jsonify({"status": "ERROR", "message": "Flag mancante"}), 400

    flag = flag.strip()
    is_valid, reason = submitter.validate_flag(flag)
    status_to_add = STATUS_PENDING if is_valid else STATUS_INVALID
    inferred_info = submitter.decode_flag_info(flag) if is_valid else None

    flag_id = database.add_flag(flag, author, service, status_to_add, inferred_info)

    if flag_id:
        logging.info(f"Flag ricevuta da {author} per {service}. Stato: {status_to_add}. Flag: {flag[:6]}...")
        if is_valid:
            return jsonify({"status": "OK", "message": "Flag added to queue", "flag_id": flag_id})
        else:
            return jsonify({"status": "WARN", "message": f"Flag received but format is invalid: {reason}", "flag_id": flag_id}), 400 # Errore client se non valida
    else:
        logging.error(f"Errore DB durante aggiunta flag: {flag[:6]}...")
        return jsonify({"status": "ERROR", "message": "Internal server error adding flag"}), 500

# --- Route UI ---
@app.route('/', methods=['GET'])
def index():
    """Pagina principale che mostra le flag e i filtri."""
    # Recupera parametri filtro dalla query string
    author_filter = request.args.get('author', '')
    service_filter = request.args.get('service', '')
    status_filter = request.args.get('status', '')

    # Recupera flag filtrate dal DB
    flags = database.get_filtered_flags(
        author=author_filter,
        service=service_filter,
        status=status_filter,
        limit=UI_FLAGS_PER_PAGE
    )

    # Recupera statistiche
    stats = database.get_stats()

    # Lista degli stati possibili per il dropdown del filtro
    possible_statuses = [STATUS_PENDING, STATUS_ACCEPTED, STATUS_REJECTED, STATUS_OLD, STATUS_ERROR, STATUS_INVALID]

    return render_template(
        'index.html',
        flags=flags,
        stats=stats,
        possible_statuses=possible_statuses,
        # Passa i valori attuali dei filtri per pre-compilare il form
        author_filter=author_filter,
        service_filter=service_filter,
        status_filter=status_filter
    )

@app.route('/api/flags_table', methods=['GET'])
def api_flags_table():
    """Restituisce solo l'HTML del corpo della tabella flag, filtrato."""
    author_filter = request.args.get('author', '')
    service_filter = request.args.get('service', '')
    status_filter = request.args.get('status', '')

    flags = database.get_filtered_flags(
        author=author_filter,
        service=service_filter,
        status=status_filter,
        limit=UI_FLAGS_PER_PAGE # Usa lo stesso limite della pagina principale
    )
    # Renderizza il template parziale con i dati filtrati
    return render_template('_flags_tbody.html', flags=flags)

@app.route('/flags/delete/<int:flag_id>', methods=['POST']) # Usa POST per sicurezza
def delete_flag_route(flag_id):
    """Route per eliminare una flag."""
    deleted_count = database.delete_flag(flag_id)
    if deleted_count > 0:
        logging.info(f"Flag ID {flag_id} eliminata correttamente.")
        # Potresti aggiungere un messaggio flash qui se vuoi
    else:
        logging.warning(f"Tentativo di eliminare flag ID {flag_id} fallito o flag non trovata.")
        # Potresti aggiungere un messaggio flash di errore qui
    # Reindirizza l'utente alla pagina principale per vedere la tabella aggiornata
    return redirect(url_for('index'))

# --- Avvio Applicazione ---
if __name__ == "__main__":
    database.init_db(app) # Inizializza DB prima di avviare

    # Avvia il thread worker in background
    worker_thread = threading.Thread(target=submission_worker, daemon=True)
    worker_thread.start()

    print(f"\n[*] Submitter UI disponibile su http://0.0.0.0:5000")
    print(f"[*] API Endpoint per ricevere flag (POST): http://0.0.0.0:5000/api/submit")
    print(f"[*]    Payload JSON: {{'flag': 'FLAG...', 'author': '...', 'service': '...'}}")
    print(f"[*]    Oppure Form Data: flag=FLAG...&author=...&service=...")
    print("[!] Premi CTRL+C per fermare.")

    try:
        app.run(host='0.0.0.0', port=5000, threaded=True) # threaded=True necessario per Flask dev server con thread
    except KeyboardInterrupt:
        print("\nInterruzione richiesta... Fermo il worker...")
        submitter_thread_stop_event.set()
        worker_thread.join(timeout=5) # Attendi che il thread finisca
        print("Submitter fermato.")
