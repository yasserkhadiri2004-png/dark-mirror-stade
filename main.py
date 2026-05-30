"""
main.py — Serveur Flask + thread webcam.
CORRECTION : voice_assistant blueprint enregistré correctement.
"""

import cv2
import json
import threading
import time
import webbrowser
import numpy as np
import os
import sys
import urllib.request
from flask import Flask, jsonify, render_template, send_from_directory
import tts_engine as tts

# ════════════════════════════════════════════════
# MODÈLE DNN VISAGE
# ════════════════════════════════════════════════
PROTO = "data/deploy.prototxt"
MODEL = "data/res10_300x300_ssd_iter_140000.caffemodel"

os.makedirs("data", exist_ok=True)

if not os.path.exists(PROTO):
    print("Téléchargement deploy.prototxt...")
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
        PROTO
    )

if not os.path.exists(MODEL):
    print("Téléchargement poids modèle DNN...")
    urllib.request.urlretrieve(
        "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel",
        MODEL
    )

detecteur_dnn = cv2.dnn.readNetFromCaffe(PROTO, MODEL)
print("Modèle DNN chargé ✔")

# ── Précharger InsightFace ────────────────────────────────────────────────────
try:
    from gender_detector import charger_modele, analyser_genre_insightface, analyser_genre_haar
    charger_modele()
    print("InsightFace chargé ✔")
except Exception as e:
    print(f"InsightFace non disponible : {e} — fallback Haar")
    from gender_detector import analyser_genre_haar
    def analyser_genre_insightface(img):
        return analyser_genre_haar(img), 0.6

# ── Profils maillots ──────────────────────────────────────────────────────────
try:
    from detector_maillot import detecter_equipe_par_profil, charger_profils
    charger_profils()
    print("Profils maillots chargés ✔")
    USE_PROFILS = True
except Exception as e:
    print(f"detector_maillot non disponible : {e}")
    USE_PROFILS = False

# ── Détecteurs Haar ───────────────────────────────────────────────────────────
YEUX    = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
SOURIRE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

# ── Données ───────────────────────────────────────────────────────────────────
with open('data/equipes.json', 'r', encoding='utf-8') as f:
    EQUIPES = json.load(f)

with open('data/tickets.json', 'r', encoding='utf-8') as f:
    BASE_TICKETS = json.load(f)

# ════════════════════════════════════════════════
# FLASK + BLUEPRINTS
# ════════════════════════════════════════════════
app = Flask(__name__, template_folder='web', static_folder='static')

# ── Enregistrement blueprint voice_assistant ──────────────────────────────────
try:
    from voice_assistant import voice_bp
    app.register_blueprint(voice_bp)
    print("Voice assistant chargé ✔")
except Exception as e:
    print(f"voice_assistant non disponible : {e}")

# ── État global ───────────────────────────────────────────────────────────────
ETAT = {
    'genre':    None,
    'maillot':  None,
    'equipe':   None,
    'drapeau':  None,
    'surnom':   None,
    'couleur':  None,
    'souriant': False,
}

_lock_etat      = threading.Lock()
derniere_equipe = None
bienvenue_dit   = False

_insightface_result   = None
_insightface_en_cours = False


def reset_etat():
    global bienvenue_dit, derniere_equipe, _insightface_result, _insightface_en_cours
    with _lock_etat:
        for k in ETAT:
            ETAT[k] = False if k == 'souriant' else None
        bienvenue_dit         = False
        derniere_equipe       = None
        _insightface_result   = None
        _insightface_en_cours = False


# ════════════════════════════════════════════════
# ROUTES FLASK
# ════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/etat')
def get_etat():
    with _lock_etat:
        return jsonify(dict(ETAT))

@app.route('/api/ticket/<code>')
def get_ticket(code):
    code = code.strip().upper()
    data = BASE_TICKETS.get(code) or generer_ticket(code)
    if data:
        threading.Thread(target=tts.annoncer_ticket, args=(data,), daemon=True).start()
        return jsonify(data)
    threading.Thread(target=tts.annoncer_invalide, daemon=True).start()
    return jsonify(None), 404

@app.route('/api/equipes')
def get_equipes():
    return jsonify(EQUIPES)

# ── Route test voice (diagnostic) ────────────────────────────────────────────
@app.route('/api/voice/test', methods=['GET'])
def test_voice():
    return jsonify({"status": "voice_assistant OK", "route": "/api/voice"})


# ════════════════════════════════════════════════
# GÉNÉRATION TICKET
# ════════════════════════════════════════════════

BLOCS = {
    'A': {'zone':'Tribune Nord - Bloc A',     'porte':'Entrée 1 - Côté Nord',     'parking':'Parking Nord P1',  'buvette':'Buvette N1', 'vestiaire':'Vestiaire A', 'hopital':'Poste Médical Nord',  'secteur':'nord'},
    'B': {'zone':'Tribune Sud - Bloc B',      'porte':'Entrée 3 - Côté Sud',      'parking':'Parking Sud P2',   'buvette':'Buvette S1', 'vestiaire':'Vestiaire B', 'hopital':'Poste Médical Sud',   'secteur':'sud'},
    'C': {'zone':'Tribune Est - Bloc C',      'porte':'Entrée 5 - Côté Est',      'parking':'Parking Est P3',   'buvette':'Buvette E1', 'vestiaire':'Vestiaire C', 'hopital':'Poste Médical Est',   'secteur':'est'},
    'D': {'zone':'Tribune Ouest - Bloc D',    'porte':'Entrée 6 - Côté Ouest',    'parking':'Parking Ouest P4', 'buvette':'Buvette O1', 'vestiaire':'Vestiaire D', 'hopital':'Poste Médical Ouest', 'secteur':'ouest'},
    'E': {'zone':'Tribune Nord-Est - Bloc E', 'porte':'Entrée 2 - Côté Nord-Est', 'parking':'Parking Nord P1',  'buvette':'Buvette N2', 'vestiaire':'Vestiaire E', 'hopital':'Poste Médical Nord',  'secteur':'nord'},
    'F': {'zone':'Tribune Sud-Est - Bloc F',  'porte':'Entrée 4 - Côté Sud-Est',  'parking':'Parking Sud P2',   'buvette':'Buvette S2', 'vestiaire':'Vestiaire F', 'hopital':'Poste Médical Sud',   'secteur':'sud'},
}

def generer_ticket(code: str) -> dict | None:
    if code.startswith('VIP'):
        num = code[3:] or '01'
        return {
            'zone':'Tribune Honneur - Loge VIP', 'rang':f'Loge VIP, Place {num}',
            'porte':'Entrée VIP - Côté Ouest',   'parking':'Parking VIP Réservé',
            'buvette':'Salon VIP - Niveau 2',    'vestiaire':'Vestiaire VIP Privé',
            'hopital':'Médecin de service VIP',  'secteur':'vip'
        }
    if len(code) >= 2 and code[0].isalpha():
        bloc = code[0].upper()
        nums = code[1:]
        if bloc not in BLOCS or not nums.isdigit():
            return None
        rang  = nums[:-2] if len(nums) >= 3 else (nums[0] if nums else '1')
        siege = nums[-2:]  if len(nums) >= 3 else (nums[1:] if len(nums) > 1 else '01')
        info  = BLOCS[bloc].copy()
        info['rang'] = f'Rang {rang}, Siège {siege}'
        return info
    return None


# ════════════════════════════════════════════════
# DÉTECTION GENRE — INSIGHTFACE ASYNC
# ════════════════════════════════════════════════

def lancer_insightface_async(frame: np.ndarray):
    global _insightface_en_cours, _insightface_result
    if _insightface_en_cours:
        return
    _insightface_en_cours = True

    def _run(img):
        global _insightface_result, _insightface_en_cours
        try:
            result = analyser_genre_insightface(img)
            genre  = result[0] if isinstance(result, tuple) else result
            if genre in ('homme', 'femme'):
                _insightface_result = genre
        except Exception as e:
            print(f"[InsightFace] Erreur : {e}")
        finally:
            _insightface_en_cours = False

    threading.Thread(target=_run, args=(frame.copy(),), daemon=True).start()


def detecter_couleur_dominante(frame, x, y, w, h):
    img_h, img_w = frame.shape[:2]
    y1 = min(y + h,     img_h)
    y2 = min(y + h * 3, img_h)
    x1 = max(x - w//2,  0)
    x2 = min(x + w + w//2, img_w)
    if y2 <= y1 or x2 <= x1:
        return None, 0
    roi = frame[y1:y2, x1:x2]
    if roi.size == 0:
        return None, 0
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    meilleure_equipe, meilleur_score = None, 0
    seuil = roi.shape[0] * roi.shape[1] * 0.10
    for nom_equipe, data in EQUIPES.items():
        score_total = 0
        for _, (low, high) in data['couleurs_hsv'].items():
            score_total += cv2.countNonZero(cv2.inRange(hsv, np.array(low), np.array(high)))
        if score_total > meilleur_score:
            meilleur_score, meilleure_equipe = score_total, nom_equipe
    return (meilleure_equipe, meilleur_score) if meilleur_score >= seuil else (None, 0)


# ════════════════════════════════════════════════
# THREAD WEBCAM
# ════════════════════════════════════════════════

def boucle_webcam():
    global derniere_equipe, bienvenue_dit, _insightface_result

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    print("Webcam démarrée ✔")

    compteur    = 0
    genre_votes = []

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        frame     = cv2.flip(frame, 1)
        compteur += 1

        if compteur % 3 == 0:
            h_f, w_f = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(
                cv2.resize(frame, (300, 300)),
                1.0, (300, 300), (104, 117, 123)
            )
            detecteur_dnn.setInput(blob)
            detections    = detecteur_dnn.forward()
            visage_trouve = False

            for i in range(detections.shape[2]):
                confiance_visage = float(detections[0, 0, i, 2])
                if confiance_visage < 0.6:
                    continue

                visage_trouve = True
                box           = detections[0, 0, i, 3:7] * np.array([w_f, h_f, w_f, h_f])
                x, y, x2, y2  = box.astype(int)
                bw, bh         = x2 - x, y2 - y
                visage_img     = frame[max(0,y):y2, max(0,x):x2]

                if visage_img.size > 0:
                    # ── ARRÊT À 3 VOTES — plus de détection après ─────────
                    if len(genre_votes) >= 3:
                        # Décision finale déjà prise — ne plus rien faire
                        pass
                    else:
                        # Haar instantané (<5ms) pour le 1er affichage
                        genre_rapide = analyser_genre_haar(visage_img)

                        # InsightFace async toutes les 6 frames
                        if compteur % 6 == 0:
                            lancer_insightface_async(visage_img)

                        genre_final = _insightface_result if _insightface_result else genre_rapide
                        genre_votes.append(genre_final)

                        nb_femme = genre_votes.count('femme')
                        nb_total = len(genre_votes)

                        if nb_total == 1:
                            genre_stable = genre_votes[0]
                            print(f"[Votes] 1/3 → {genre_stable} (affichage immédiat)")
                        elif nb_total == 2:
                            genre_stable = 'femme' if nb_femme == 2 else 'homme'
                            print(f"[Votes] 2/3 → {genre_stable}")
                        else:
                            genre_stable = 'femme' if nb_femme >= 2 else 'homme'
                            print(f"[Votes] 3/3 FINAL → {genre_stable} ✔ — détection arrêtée")

                        with _lock_etat:
                            ancien_genre  = ETAT['genre']
                            ETAT['genre'] = genre_stable

                        if ancien_genre is None and not bienvenue_dit:
                            bienvenue_dit = True
                            _g = genre_stable
                            _e = ETAT.get('maillot')
                            def _bienvenue(g=_g, e=_e):
                                time.sleep(1)
                                tts.annoncer_bienvenue(g, e)
                            threading.Thread(target=_bienvenue, daemon=True).start()

                # Détection maillot toutes les 9 frames
                if compteur % 9 == 0:
                    if USE_PROFILS:
                        equipe, confiance = detecter_equipe_par_profil(frame, x, y, bw, bh, seuil=0.45)
                        match = equipe and confiance > 0.3
                    else:
                        equipe, score = detecter_couleur_dominante(frame, x, y, bw, bh)
                        match = equipe is not None

                    if match:
                        info = EQUIPES.get(equipe)
                        if info:
                            with _lock_etat:
                                ETAT['equipe']  = equipe
                                ETAT['maillot'] = info['nom']
                                ETAT['drapeau'] = info['drapeau']
                                ETAT['surnom']  = info['surnom']
                                ETAT['couleur'] = info['couleur_hex']
                            if equipe != derniere_equipe:
                                derniere_equipe = equipe
                                _nom = info['nom']
                                def _dire_equipe(nom=_nom):
                                    time.sleep(3)
                                    tts.parler(f"Je vois que vous supportez {nom} !")
                                threading.Thread(target=_dire_equipe, daemon=True).start()
                break

            if not visage_trouve and bienvenue_dit:
                reset_etat()
                genre_votes.clear()
                print("Personne → reset")

        if compteur >= 600:
            compteur = 0

        time.sleep(0.02)

    cap.release()


# ════════════════════════════════════════════════
# LANCEMENT
# ════════════════════════════════════════════════

if __name__ == '__main__':
    # Nettoyer anciens fichiers TTS
    sounds_dir = 'static/sounds'
    if os.path.exists(sounds_dir):
        for f in os.listdir(sounds_dir):
            if f.startswith('tts_') and f.endswith('.mp3'):
                try: os.remove(os.path.join(sounds_dir, f))
                except OSError: pass

    threading.Thread(target=boucle_webcam, daemon=True).start()
    threading.Timer(1.5, lambda: webbrowser.open('http://localhost:5000')).start()

    print("=" * 50)
    print("  Serveur démarré → http://localhost:5000")
    print("  Test voice → http://localhost:5000/api/voice/test")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=False)
