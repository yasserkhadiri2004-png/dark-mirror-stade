"""
gender_detector.py — Détection de genre via InsightFace.
CORRECTION : biais homme quand confiance faible (barbe, lunettes, masque).

Logique :
  - confiance > 0.85 → résultat InsightFace tel quel
  - confiance 0.60-0.85 → si résultat = femme, vérifier avec Haar
  - confiance < 0.60 → forcer 'homme' (visage partiellement caché)
  - Fenêtre de votes élargie à 10 avec seuil asymétrique (7/10 pour femme)
"""

import sys
import cv2
import numpy as np

# ── InsightFace ───────────────────────────────────────────────────────────────
_app_insightface = None

def charger_modele():
    global _app_insightface
    if _app_insightface is not None:
        return _app_insightface
    try:
        from insightface.app import FaceAnalysis
        app = FaceAnalysis(
            name      = 'buffalo_sc',
            providers = ['CPUExecutionProvider']
        )
        app.prepare(ctx_id=0, det_size=(320, 320))
        _app_insightface = app
        print("[InsightFace] Modèle chargé ✔")
        return app
    except ImportError:
        print("[InsightFace] Non installé → pip install insightface onnxruntime")
        return None
    except Exception as e:
        print(f"[InsightFace] Erreur : {e}")
        return None


def analyser_genre_haar(image: np.ndarray) -> tuple[str, float]:
    """
    Heuristique Haar — retourne (genre, confiance_approx).
    Confiance basse car peu de critères.
    """
    h, w  = image.shape[:2]
    ratio = w / h if h > 0 else 1
    gris  = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gris  = cv2.equalizeHist(gris)

    SOURIRE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
    YEUX    = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

    sourires = SOURIRE.detectMultiScale(gris, 1.7, 20, minSize=(25, 25))
    yeux     = YEUX.detectMultiScale(gris, 1.1, 5,  minSize=(15, 15))

    sh = 2 if ratio > 0.88 else 0
    sf = 0 if ratio > 0.88 else 2
    sf += 1 if len(sourires) > 0 else 0
    sh += 1 if len(sourires) == 0 else 0
    sf += 1 if len(yeux) >= 2 else 0

    total = sh + sf
    if total == 0:
        return 'homme', 0.3

    if sh >= sf:
        return 'homme', round(sh / total, 2)
    else:
        return 'femme', round(sf / total, 2)


def analyser_genre_insightface(image: np.ndarray) -> tuple[str, float]:
    """
    Analyse genre avec InsightFace + correction biais homme.

    Règles de confiance :
      > 0.85 → résultat direct
      0.60-0.85 + femme → double vérification avec Haar
      < 0.60 → homme (visage caché : barbe, lunettes, masque)

    Retourne (genre, confiance).
    """
    app = charger_modele()
    if app is None:
        return analyser_genre_haar(image)

    try:
        faces = app.get(image)

        if not faces:
            # Pas de visage détecté → fallback Haar
            return analyser_genre_haar(image)

        face      = max(faces, key=lambda f: f.det_score)
        det_score = float(face.det_score)
        genre_raw = 'homme' if face.gender == 1 else 'femme'

        # ── Règle 1 : confiance haute → résultat direct ──────────────────────
        if det_score >= 0.85:
            print(f"[InsightFace] {genre_raw} confiance={det_score:.2f} (direct)")
            return genre_raw, det_score

        # ── Règle 2 : confiance moyenne + femme → double vérification ────────
        if det_score >= 0.60 and genre_raw == 'femme':
            genre_haar, conf_haar = analyser_genre_haar(image)
            if genre_haar == 'homme':
                # Haar dit homme → probablement barbe ou lunettes
                print(f"[InsightFace] correction homme (InsightFace={det_score:.2f}, Haar=homme)")
                return 'homme', 0.65
            else:
                # Les deux disent femme → confiance renforcée
                print(f"[InsightFace] femme confirmée (InsightFace+Haar)")
                return 'femme', min(det_score + 0.1, 1.0)

        # ── Règle 3 : confiance faible → biais homme ─────────────────────────
        if det_score < 0.60:
            print(f"[InsightFace] confiance faible ({det_score:.2f}) → biais homme")
            return 'homme', 0.55

        # Cas restant (homme, confiance moyenne)
        print(f"[InsightFace] {genre_raw} confiance={det_score:.2f}")
        return genre_raw, det_score

    except Exception as e:
        print(f"[InsightFace] Erreur : {e}")
        return analyser_genre_haar(image)


def analyser_genre_depuis_fichier(image_path: str) -> str:
    """Point d'entrée fichier — retourne uniquement le genre (str)."""
    img = cv2.imread(image_path)
    if img is None:
        return 'homme'
    genre, _ = analyser_genre_insightface(img)
    return genre


# ── Sous-processus ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) > 1:
        genre = analyser_genre_depuis_fichier(sys.argv[1])
        print(genre)
        sys.stdout.flush()
    else:
        print("Usage : python gender_detector.py <chemin_image>", file=sys.stderr)
        sys.exit(1)
