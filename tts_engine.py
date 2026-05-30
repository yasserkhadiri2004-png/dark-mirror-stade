"""
tts_engine.py — Moteur TTS ElevenLabs pour Dark Mirror.
Voix : Loïc (homme) + Alimata (femme) — naturelles et professionnelles.
"""

import requests
import threading
import os
import time

# ── Configuration ElevenLabs ──────────────────────────────────────────────────
API_KEY = "sk_fdb0a0d486e04b562f74d754302c72ed1c95647e0e29f7d2"

VOICE_ID_HOMME = "onwK4e9ZLuTAKqWW03F9"   # Daniel  (homme français)
VOICE_ID_FEMME = "XB0fDUnXU5powFXDhCwa"   # Charlotte (femme française)

# Paramètres vocaux optimisés pour annonces stade
VOICE_SETTINGS_HOMME = {
    "stability":         0.65,
    "similarity_boost":  0.80,
    "style":             0.15,
    "use_speaker_boost": True
}

VOICE_SETTINGS_FEMME = {
    "stability":         0.58,
    "similarity_boost":  0.82,
    "style":             0.20,
    "use_speaker_boost": True
}

HEADERS = {
    "xi-api-key":   API_KEY,
    "Content-Type": "application/json"
}

MODEL_ID = "eleven_multilingual_v2"

# ── Messages ──────────────────────────────────────────────────────────────────
MESSAGES = {
    'bienvenue_homme': (
        "Bienvenue monsieur au stade Moulay Abdellah de Rabat ! "
        "Je suis votre assistant virtuel. Je suis là pour vous guider."
    ),
    'bienvenue_femme': (
        "Bienvenue madame au stade Moulay Abdellah de Rabat ! "
        "Je suis votre assistante virtuelle. Je suis là pour vous guider."
    ),
    'equipe':  "Je vois que vous supportez {equipe} ! Allez les {surnom} !",
    'invalid': "Ticket non reconnu. Veuillez vérifier votre code et réessayer.",
}


# ════════════════════════════════════════════════
# CORE TTS
# ════════════════════════════════════════════════

def generer_audio(texte: str, voice_id: str = None, settings: dict = None) -> str | None:
    """
    Appelle ElevenLabs et sauvegarde le MP3.
    Retourne le chemin du fichier ou None en cas d'erreur.
    """
    if not voice_id:
        voice_id = VOICE_ID_HOMME
    if not settings:
        settings = VOICE_SETTINGS_HOMME

    url     = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text":           texte,
        "model_id":       MODEL_ID,
        "voice_settings": settings
    }

    try:
        r = requests.post(url, headers=HEADERS, json=payload, timeout=15)
        if r.status_code == 200:
            os.makedirs("static/sounds", exist_ok=True)
            chemin = f"static/sounds/tts_{int(time.time() * 1000)}.mp3"
            with open(chemin, "wb") as f:
                f.write(r.content)
            return chemin
        else:
            print(f"[TTS] Erreur ElevenLabs {r.status_code} : {r.text[:150]}")
            return None
    except requests.exceptions.Timeout:
        print("[TTS] Timeout ElevenLabs")
        return None
    except Exception as e:
        print(f"[TTS] Erreur réseau : {e}")
        return None


def jouer_audio(chemin: str):
    """Lecture MP3 selon l'OS."""
    if not chemin or not os.path.exists(chemin):
        return
    try:
        if os.name == 'nt':
            os.system(f'start "" "{chemin}"')
        elif hasattr(os, 'uname') and os.uname().sysname == 'Darwin':
            os.system(f'afplay "{chemin}"')
        else:
            os.system(
                f'mpg123 -q "{chemin}" 2>/dev/null || '
                f'ffplay -nodisp -autoexit "{chemin}" 2>/dev/null'
            )
    except Exception as e:
        print(f"[TTS] Lecture impossible : {e}")


def parler(texte: str, genre: str = None):
    """Génère et joue la voix dans un thread séparé (non bloquant)."""
    if genre == 'femme':
        voice_id = VOICE_ID_FEMME
        settings = VOICE_SETTINGS_FEMME
    else:
        voice_id = VOICE_ID_HOMME
        settings = VOICE_SETTINGS_HOMME

    def _run():
        print(f"[TTS] {texte[:80]}{'...' if len(texte) > 80 else ''}")
        chemin = generer_audio(texte, voice_id, settings)
        if chemin:
            jouer_audio(chemin)

    threading.Thread(target=_run, daemon=True).start()


# ════════════════════════════════════════════════
# ANNONCES MÉTIER
# ════════════════════════════════════════════════

def annoncer_ticket(ticket: dict, genre: str = None):
    """
    Annonce vocale complète du ticket.
    Lit : zone, rang, porte, parking, buvette, vestiaire.
    """
    zone      = ticket.get('zone',      'zone inconnue')
    rang      = ticket.get('rang',      'rang inconnu')
    porte     = ticket.get('porte',     'entrée inconnue')
    parking   = ticket.get('parking',   'parking inconnu')
    buvette   = ticket.get('buvette',   'buvette inconnue')
    vestiaire = ticket.get('vestiaire', 'vestiaire inconnu')

    texte = (
        f"Bienvenue au stade Moulay Abdellah ! "
        f"Votre place se trouve en {zone}, au {rang}. "
        f"Veuillez entrer par {porte}. "
        f"Votre parking est le {parking}. "
        f"La buvette la plus proche est {buvette}. "
        f"Les vestiaires se trouvent au {vestiaire}."
    )
    parler(texte, genre)


def annoncer_bienvenue(genre: str = None, equipe: str = None):
    """Message d'accueil personnalisé."""
    cle = 'bienvenue_femme' if genre == 'femme' else 'bienvenue_homme'
    parler(MESSAGES[cle], genre)

    if equipe:
        time.sleep(3.5)
        msg = MESSAGES['equipe'].format(equipe=equipe, surnom=equipe)
        parler(msg, genre)


def annoncer_invalide():
    parler(MESSAGES['invalid'])


# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Test TTS ElevenLabs...")
    parler("Bienvenue monsieur au stade Moulay Abdellah de Rabat. Bon match !", 'homme')
    time.sleep(8)

    print("Test ticket...")
    annoncer_ticket({
        'zone':      'Tribune Nord - Bloc A',
        'rang':      'Rang 2, Siège 15',
        'porte':     'Entrée 1 - Côté Nord',
        'parking':   'Parking Nord P1',
        'buvette':   'Buvette N1',
        'vestiaire': 'Vestiaire A - Niveau 0',
    }, genre='homme')
    time.sleep(12)
    print("Test terminé !")
