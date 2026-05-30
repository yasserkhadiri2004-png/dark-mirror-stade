"""
voice_assistant.py — Assistant vocal avec RAG intégré.
CORRECTION : Blueprint correctement défini et routes fonctionnelles.
"""

import os
import time
import tempfile
import requests
from flask import Blueprint, request, jsonify
import tts_engine as tts

# ── Blueprint Flask ───────────────────────────────────────────────────────────
voice_bp = Blueprint('voice', __name__)

# ── Clés API ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY    = os.environ.get("OPENAI_API_KEY",    "")

# ── Mots-clés RAG ─────────────────────────────────────────────────────────────
MOTS_RAG = [
    "hôtel", "hotel", "restaurant", "manger", "café", "cafe",
    "taxi", "bus", "transport", "parking", "garer",
    "pharmacie", "médicament", "banque", "distributeur", "atm",
    "supermarché", "magasin", "mosquée", "prière",
    "près", "proche", "autour", "à côté", "recommande",
    "hôpital", "urgence", "dormir", "nuit", "chambre",
]

def necessite_rag(question: str) -> bool:
    return any(m in question.lower() for m in MOTS_RAG)


# ── Prompt système stade ──────────────────────────────────────────────────────
SYSTEM_STADE = """Tu es Nour, assistante virtuelle du Stade Moulay Abdellah de Rabat.
Tu réponds UNIQUEMENT en français, de façon concise (2-3 phrases max), chaleureuse et professionnelle.
Tu aides pour : place, entrées, parkings, buvettes, toilettes, postes médicaux, règles du stade.
Si la question ne concerne pas le stade ou les services proches, dis poliment que tu ne traites que ces sujets."""


def reponse_claude(question: str, genre: str, equipe: str, contexte_rag: str = "") -> str:
    """Appel à Claude Haiku avec contexte."""
    if not ANTHROPIC_API_KEY:
        return reponse_fallback(question)

    ctx = ""
    if genre:
        ctx += f"Visiteur : {'femme' if genre == 'femme' else 'homme'}. "
    if equipe:
        ctx += f"Supporte {equipe}. "

    system = SYSTEM_STADE
    if contexte_rag:
        system += f"\n\nDONNÉES LIEUX AUTOUR DU STADE :\n{contexte_rag}"
    if ctx:
        system += f"\n\nContexte visiteur : {ctx}"

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type":      "application/json"
            },
            json={
                "model":      "claude-haiku-4-5-20251001",
                "max_tokens": 200,
                "system":     system,
                "messages":   [{"role": "user", "content": question}]
            },
            timeout=10
        )
        if r.status_code == 200:
            return r.json()["content"][0]["text"].strip()
        print(f"[Claude] {r.status_code} : {r.text[:80]}")
        return reponse_fallback(question)
    except Exception as e:
        print(f"[Claude] Erreur : {e}")
        return reponse_fallback(question)


def reponse_fallback(question: str) -> str:
    """Réponses pré-définies si Claude indisponible."""
    q = question.lower()
    if any(m in q for m in ["place", "siège", "rang", "bloc", "tribune", "où suis"]):
        return "Pour trouver votre place, repérez le code sur votre ticket et suivez la signalétique depuis l'entrée indiquée."
    if any(m in q for m in ["parking", "voiture", "garer", "stationner"]):
        return "Les parkings sont aux quatre côtés du stade. Votre ticket précise le parking attribué."
    if any(m in q for m in ["buvette", "manger", "boire", "nourriture", "restaur"]):
        return "Les buvettes sont situées à chaque niveau du stade. La plus proche dépend de votre tribune."
    if any(m in q for m in ["toilette", "wc", "sanitaire"]):
        return "Les sanitaires se trouvent à chaque entrée de tribune, aux niveaux 0 et 1."
    if any(m in q for m in ["médecin", "urgence", "secours", "blessé", "malade"]):
        return "Le poste médical principal est côté Nord. En cas d'urgence, signalez-vous à un agent de sécurité."
    if any(m in q for m in ["entrée", "porte", "accès", "rentrer", "entrer"]):
        return "Chaque entrée est indiquée par une lettre sur votre ticket. Suivez la signalétique colorée."
    if any(m in q for m in ["wifi", "internet", "réseau"]):
        return "WiFi gratuit disponible. Réseau : Stade_MAB, sans mot de passe."
    if any(m in q for m in ["bonjour", "salut", "bonsoir", "hello", "salam"]):
        return "Bonjour ! Je suis Nour, votre assistante au stade Moulay Abdellah. Comment puis-je vous aider ?"
    if any(m in q for m in ["hôtel", "hotel", "dormir"]):
        return "Plusieurs hôtels se trouvent à moins de 2km du stade. Puis-je vous aider à trouver autre chose ?"
    if any(m in q for m in ["taxi", "transport", "bus"]):
        return "Des taxis sont disponibles aux sorties principales du stade. Des navettes sont également organisées."
    return "Je suis votre assistante au stade Moulay Abdellah. Posez-moi vos questions sur votre place, les entrées ou les services disponibles !"


def transcrire_whisper(fichier: str) -> str | None:
    """Transcription audio via Whisper OpenAI."""
    if not OPENAI_API_KEY:
        return None
    try:
        with open(fichier, "rb") as f:
            r = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={"file": (os.path.basename(fichier), f, "audio/webm")},
                data={"model": "whisper-1", "language": "fr"},
                timeout=15
            )
        return r.json().get("text", "").strip() if r.status_code == 200 else None
    except Exception as e:
        print(f"[Whisper] {e}")
        return None


# ════════════════════════════════════════════════
# ROUTES
# ════════════════════════════════════════════════

@voice_bp.route('/api/voice', methods=['POST'])
def traiter_voix():
    """
    Reçoit une question (JSON ou audio) et retourne une réponse vocale.
    Body JSON  : { "texte": "votre question" }
    Body form  : fichier audio (multipart)
    Retourne   : { "question": "...", "texte": "...", "audio_url": "..." }
    """
    # Récupérer l'état caméra
    try:
        from main import ETAT
        genre  = ETAT.get('genre')
        equipe = ETAT.get('maillot')
    except Exception:
        genre, equipe = None, None

    # Récupérer la question
    question = None

    if request.is_json:
        data = request.get_json(silent=True) or {}
        question = data.get('texte', '').strip()
    elif 'audio' in request.files:
        f   = request.files['audio']
        tmp = tempfile.NamedTemporaryFile(suffix='.webm', delete=False)
        f.save(tmp.name); tmp.close()
        question = transcrire_whisper(tmp.name)
        os.unlink(tmp.name)

    if not question:
        return jsonify({"erreur": "Aucune question reçue"}), 400

    print(f"[Voice] ❓ {question}")

    # RAG ou réponse stade
    contexte_rag = ""
    if necessite_rag(question):
        try:
            from rag_engine import rechercher_lieux, construire_contexte_rag
            lieux = rechercher_lieux(question, nb_max=3)
            contexte_rag = construire_contexte_rag(lieux)
            print(f"[Voice] RAG activé — {len(lieux)} lieux trouvés")
        except Exception as e:
            print(f"[RAG] Non disponible : {e}")

    reponse = reponse_claude(question, genre, equipe, contexte_rag)
    print(f"[Voice] 💬 {reponse}")

    # Synthèse ElevenLabs
    audio_url = None
    try:
        # Compatibilité ancienne et nouvelle version de tts_engine
        voice_id = getattr(tts, 'VOICE_ID_FEMME', 'XB0fDUnXU5powFXDhCwa') if genre == 'femme'                    else getattr(tts, 'VOICE_ID_HOMME', 'onwK4e9ZLuTAKqWW03F9')

        settings = {
            "stability":         0.60,
            "similarity_boost":  0.80,
            "style":             0.20,
            "use_speaker_boost": True
        }

        # Essayer generer_audio avec settings, sinon sans
        try:
            chemin = tts.generer_audio(reponse, voice_id, settings)
        except TypeError:
            chemin = tts.generer_audio(reponse, voice_id)

        if chemin:
            audio_url = '/' + chemin.replace('\\', '/')
    except Exception as e:
        print(f"[TTS] Erreur : {e}")
        # Fallback : parler sans audio_url
        tts.parler(reponse, genre)

    return jsonify({
        "question":  question,
        "texte":     reponse,
        "audio_url": audio_url,
    })


@voice_bp.route('/api/voice', methods=['GET'])
def test_voice_get():
    """Route GET pour tester que le blueprint est bien chargé."""
    return jsonify({"status": "voice_assistant OK", "methode": "POST pour poser une question"})
