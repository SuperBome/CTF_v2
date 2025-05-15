import requests
import json
import time
from config import (GAMESERVER_URL, TEAM_TOKEN, REQUESTS_TIMEOUT, FLAG_REGEX,
                    SERVER_STATUS_MAP, STATUS_ERROR, STATUS_INVALID)

def decode_flag_info(flag):
    """Tenta di decodificare round/team/service dalla flag."""
    try:
        # Questa logica dipende dal formato specifico, adattala se necessario
        # Esempio basato sul codice originale:
        # round = int(flag[0:2], 36)
        # team = int(flag[2:4], 36)
        # service = int(flag[4:6], 36)
        # return {'round': round, 'team': team, 'service': service}
        # Per ora, mettiamo placeholder se la logica non è confermata
        return {'round': None, 'team': None, 'service': None} # DA VERIFICARE/ADATTARE
    except Exception:
        return None

def validate_flag(flag):
    """Verifica il formato della flag."""
    if isinstance(flag, str) and FLAG_REGEX.match(flag):
        return True, "Valid format"
    return False, "Invalid format (doesn't match regex)"

def submit_flags_batch(flags_list):
    """
    Invia un batch di flag stringhe al Game Server.
    Restituisce un dizionario {flag_string: (status, server_response_dict)}
    """
    results = {}
    if not flags_list:
        return results

    print(f"Invio batch di {len(flags_list)} flag a {GAMESERVER_URL}")
    headers = {
        'X-Team-Token': TEAM_TOKEN,
        'Content-Type': 'application/json'
    }
    payload = json.dumps(flags_list)

    try:
        response = requests.post(  # <-- USA POST
            GAMESERVER_URL,
            headers=headers,
            data=payload,
            timeout=REQUESTS_TIMEOUT
        )
        response.raise_for_status() # Errore per 4xx/5xx

        response_data = response.json()
        print(f"Risposta Server: {response_data}")

        if isinstance(response_data, list):
             # Assumiamo che la risposta sia una lista di dict {"flag": "...", "status": "..."}
             # e che l'ordine corrisponda (ma verifichiamo per sicurezza)
            server_results = {item.get('flag'): item for item in response_data if isinstance(item, dict)}

            for flag_str in flags_list:
                if flag_str in server_results:
                    res_item = server_results[flag_str]
                    server_status = res_item.get('status')
                    internal_status = SERVER_STATUS_MAP.get(server_status, STATUS_ERROR)
                    results[flag_str] = (internal_status, json.dumps(res_item)) # Salva risposta come JSON string
                else:
                    # La flag inviata non è presente nella risposta? Strano.
                    print(f"WARN: Flag {flag_str} inviata ma non trovata nella risposta.")
                    results[flag_str] = (STATUS_ERROR, 'Flag not found in server response')

        else:
            print(f"ERRORE: Risposta server non è una lista: {response_data}")
            for flag_str in flags_list:
                results[flag_str] = (STATUS_ERROR, 'Invalid server response format (not a list)')

    except requests.exceptions.Timeout:
        print("ERRORE: Timeout invio flag")
        for flag_str in flags_list:
            results[flag_str] = (STATUS_ERROR, 'Submission timed out')
    except requests.exceptions.RequestException as e:
        print(f"ERRORE: Errore richiesta HTTP: {e}")
        error_msg = f'HTTP Error: {e}'
        if e.response is not None:
             error_msg += f' - Response: {e.response.text[:200]}' # Logga parte della risposta errata
        for flag_str in flags_list:
             results[flag_str] = (STATUS_ERROR, error_msg)
    except json.JSONDecodeError:
        print(f"ERRORE: Risposta server non è JSON valido: {response.text[:200]}")
        for flag_str in flags_list:
             results[flag_str] = (STATUS_ERROR, 'Invalid JSON response from server')
    except Exception as e:
        print(f"ERRORE: Errore imprevisto durante invio: {e}")
        for flag_str in flags_list:
            results[flag_str] = (STATUS_ERROR, f'Unexpected error: {e}')

    return results
