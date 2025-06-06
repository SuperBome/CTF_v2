# bulk_sender.py
import requests
import argparse
import sys

# --- CONFIGURAZIONE ---
# Questo URL deve puntare all'IP e porta del submitter.
# Se il submitter gira sulla stessa macchina, localhost va bene.
# Se gira su un'altra macchina nella rete, metti l'IP di quella macchina.
DEFAULT_SUBMITTER_URL = "http://192.168.1.150:5000/api/submit"
DEFAULT_AUTHOR = "bulk_sender"
DEFAULT_SERVICE = "unknown_bulk"

def send_single_flag(flag, author, service, submitter_url):
    """Invia una singola flag al submitter."""
    payload = {
        "flag": flag.strip(),
        "author": author,
        "service": service
    }
    try:
        response = requests.post(submitter_url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"SUCCESS: Flag '{flag[:10]}...' (Autore: {author}, Servizio: {service}). Risposta submitter: {response.json()}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"HTTP ERROR per flag '{flag[:10]}...': {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        print(f"ERROR invio flag '{flag[:10]}...': {e}")
    return False

def main():
    parser = argparse.ArgumentParser(description="Invia flag al CTF Submitter.")
    parser.add_argument(
        "-f", "--flags",
        nargs='+',
        help="Una o più flag da inviare direttamente dalla riga di comando."
    )
    parser.add_argument(
        "-i", "--input-file",
        type=str,
        help="File contenente una flag per riga da inviare."
    )
    parser.add_argument(
        "-a", "--author",
        type=str,
        default=DEFAULT_AUTHOR,
        help=f"Autore per queste flag (default: {DEFAULT_AUTHOR})"
    )
    parser.add_argument(
        "-s", "--service",
        type=str,
        default=DEFAULT_SERVICE,
        help=f"Servizio per queste flag (default: {DEFAULT_SERVICE})"
    )
    parser.add_argument(
        "-u", "--url",
        type=str,
        default=DEFAULT_SUBMITTER_URL,
        help=f"URL dell'endpoint API del submitter (default: {DEFAULT_SUBMITTER_URL})"
    )

    args = parser.parse_args()

    flags_to_send = []

    if args.flags:
        flags_to_send.extend(args.flags)

    if args.input_file:
        try:
            with open(args.input_file, 'r') as f:
                for line in f:
                    flag = line.strip()
                    if flag: # Ignora righe vuote
                        flags_to_send.append(flag)
            print(f"Lette {len(flags_to_send) - (len(args.flags) if args.flags else 0)} flag dal file '{args.input_file}'.")
        except FileNotFoundError:
            print(f"ERRORE: File '{args.input_file}' non trovato.")
            sys.exit(1)
        except Exception as e:
            print(f"ERRORE: Impossibile leggere il file '{args.input_file}': {e}")
            sys.exit(1)

    if not flags_to_send:
        print("Nessuna flag da inviare. Usa --flags o --input-file.")
        parser.print_help()
        sys.exit(1)

    print(f"\nInvio di {len(flags_to_send)} flag al submitter a {args.url}...")
    print(f"Autore impostato: {args.author}, Servizio impostato: {args.service}\n")

    success_count = 0
    fail_count = 0

    for flag_value in flags_to_send:
        if send_single_flag(flag_value, args.author, args.service, args.url):
            success_count += 1
        else:
            fail_count += 1

    print(f"\n--- Riepilogo ---")
    print(f"Flag inviate con successo: {success_count}")
    print(f"Flag fallite: {fail_count}")

if __name__ == "__main__":
    main()