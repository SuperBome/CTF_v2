Questo script (sender.py) permette di inviare facilmente una o più flag al nostro Submitter Web centrale.

## Prerequisiti ##
Libreria requests: Questo script necessita della libreria Python requests.
pip install requests

In caso di problemi creare un venv ed installarlo lì.

## Come Usare sender.py ##
Lo script va eseguito da terminale.

## Sintassi Generale ##
python3 sender.py [opzioni]

## Opzioni Principali: ##

--flags FLAG1 [FLAG2 ...] o -f FLAG1 [FLAG2 ...]
Invia una o più flag specificate direttamente sulla riga di comando.
Esempio: -f "FLAGMIA1..." "FLAGMIA2..."

--input-file NOME_FILE o -i NOME_FILE
Specifica un file di testo da cui leggere le flag. Il file deve contenere una flag per riga.
Esempio: -i mie_flag.txt

--author NOME_AUTORE o -a NOME_AUTORE
Imposta l'autore (es. il tuo nome o il nome del tuo exploit) per le flag inviate in questo batch. Questo apparirà nella UI del Submitter.
Default: bulk_sender
Esempio: -a "exploit_web_maria"

--service NOME_SERVIZIO o -s NOME_SERVIZIO
Imposta il nome del servizio target per le flag inviate in questo batch. Questo apparirà nella UI del Submitter.
Default: unknown_bulk
Esempio: -s "ServizioLoginV1"

--url URL_SUBMITTER_API o -u URL_SUBMITTER_API
Specifica l'URL completo dell'endpoint API del nostro Submitter Web.
Importante: Dovrai usare l'IP della macchina dove gira il Submitter se non è in esecuzione sul tuo PC.
Default: http://localhost:5000/api/submit
Esempio (se il Submitter è su 192.168.1.150): -u http://192.168.1.150:5000/api/submit

--help o -h
Mostra il messaggio di aiuto con tutte le opzioni.

# Esempi di Utilizzo #

## 1. Inviare una singola flag specificando autore e servizio 
python3 sender.py -f "FLAGUNICA1234567890ABCDEF01234=" -a "MarioR" -s "SecureChat"

## 2. Inviare più flag dalla riga di comando 
python3 sender.py -f "FLAGABC..." "FLAGXYZ..." -a "ExploitSuper" -s "WebServer"

## 3. Inviare flag al Submitter tramite file txt
python3 sender.py -i flags.txt -a "Pippo" -s "AuthService" -u http://192.168.1.150:5000/api/submit

## Cosa Succede Quando lo Esegui 
Lo script leggerà le flag che hai specificato. Per ogni flag, tenterà di inviarla al Submitter Web.
Vedrai un messaggio SUCCESS o ERROR per ogni flag inviata.
Puoi controllare lo stato dettagliato (Accepted, Rejected, Old, ecc.) e la risposta del Game Server guardando la UI del Submitter Web (http://<IP_SUBMITTER>:5000).

## Note Importanti 
URL del Submitter: Chiedi al responsabile del Submitter qual è l'indirizzo IP corretto della macchina dove è in esecuzione il Submitter Web per impostare l'opzione -u correttamente. Se non specificato, tenterà di inviare a localhost.
Formato Flag: Lo script sender.py non valida il formato della flag; la validazione avviene sul Submitter Web. Invia le flag così come le trovi.
Autore e Servizio: Fornire informazioni accurate per --author e --service aiuta tutti a tracciare meglio l'efficacia dei vari exploit e chi ha trovato cosa.
