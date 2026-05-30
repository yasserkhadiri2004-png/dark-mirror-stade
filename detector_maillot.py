"""
detector_maillot.py — Détection de maillot basée sur la comparaison
d'histogrammes HSV avec les profils construits depuis des vraies images.

Beaucoup plus précis que la détection par plages HSV fixes.
Utilise la distance de Bhattacharyya entre histogrammes.
"""

import cv2
import numpy as np
import json
import os

# ── Charger les profils ───────────────────────────
_PROFILS = None
_PROFILS_PATH = "data/maillots_profiles.json"

def charger_profils():
    global _PROFILS
    if _PROFILS is not None:
        return _PROFILS
    if not os.path.exists(_PROFILS_PATH):
        print(f"[Maillot] ⚠ Profils manquants — lancez build_dataset.py")
        return {}
    with open(_PROFILS_PATH, 'r', encoding='utf-8') as f:
        _PROFILS = json.load(f)
    print(f"[Maillot] ✔ {len(_PROFILS)} profils chargés")
    return _PROFILS


def extraire_hist_roi(frame: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray | None:
    """
    Extrait l'histogramme HSV de la zone torse du visiteur.
    Zone : entre le cou (y+h) et le bas du cadre (y+h*3).
    """
    img_h, img_w = frame.shape[:2]

    # Zone torse : sous le visage
    y1 = min(y + h,       img_h)
    y2 = min(y + h * 3,   img_h)
    x1 = max(x - w // 2,  0)
    x2 = min(x + w + w // 2, img_w)

    if y2 - y1 < 20 or x2 - x1 < 20:
        return None

    roi = frame[y1:y2, x1:x2]
    if roi.size == 0:
        return None

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Masque : éliminer fond très sombre et très clair
    masque = cv2.inRange(hsv,
        np.array([0,  25,  40]),
        np.array([180, 255, 235])
    )

    # Histogramme H sur 18 bins normalisé
    hist = cv2.calcHist([hsv], [0], masque, [18], [0, 180])
    if hist.sum() < 50:
        return None

    hist = hist / hist.sum()
    return hist.flatten()


def distance_histogramme(h1: np.ndarray, h2: list) -> float:
    """
    Distance de Bhattacharyya entre deux histogrammes.
    0 = identiques, 1 = complètement différents.
    """
    h2_arr = np.array(h2, dtype=np.float32).reshape(-1, 1)
    h1_arr = h1.astype(np.float32).reshape(-1, 1)
    return cv2.compareHist(h1_arr, h2_arr, cv2.HISTCMP_BHATTACHARYYA)


def detecter_equipe_par_profil(frame: np.ndarray,
                                x: int, y: int, w: int, h: int,
                                seuil: float = 0.45) -> tuple[str | None, float]:
    """
    Compare l'histogramme du torse du visiteur aux profils de maillots.

    Returns:
        (nom_equipe, score_confiance) ou (None, 0)
        Score : 0 = pas de match, 1 = match parfait
    """
    profils = charger_profils()
    if not profils:
        return None, 0.0

    hist_visiteur = extraire_hist_roi(frame, x, y, w, h)
    if hist_visiteur is None:
        return None, 0.0

    meilleure_equipe = None
    meilleure_distance = 1.0

    for cle, profil in profils.items():
        dist = distance_histogramme(hist_visiteur, profil['hist_h'])
        if dist < meilleure_distance:
            meilleure_distance = dist
            meilleure_equipe   = cle

    # Convertir distance en score de confiance (0→1)
    confiance = max(0.0, 1.0 - meilleure_distance / seuil)

    if meilleure_distance > seuil:
        return None, 0.0

    return meilleure_equipe, round(confiance, 2)


def ajouter_equipe_custom(cle: str, nom: str, surnom: str,
                           drapeau: str, couleur_hex: str,
                           images_paths: list[str]):
    """
    Permet d'ajouter une équipe depuis vos propres photos de maillot.
    Usage : ajouter_equipe_custom("belgique", "Belgique", "Les Diables Rouges",
                                   "🇧🇪", "#000000", ["maillot_belgique.jpg"])
    """
    from build_dataset import extraire_profil_hsv
    import time as _t

    profils = charger_profils()
    histogrammes = []

    for chemin in images_paths:
        profil = extraire_profil_hsv(chemin)
        if profil:
            histogrammes.append(profil)
            print(f"  ✔ {chemin} analysé")

    if not histogrammes:
        print("✗ Aucune image valide")
        return

    hist_moyen = np.mean([p['hist_h'] for p in histogrammes], axis=0).tolist()
    profils[cle] = {
        "nom":         nom,
        "surnom":      surnom,
        "drapeau":     drapeau,
        "couleur_hex": couleur_hex,
        "h_moyen":     round(float(np.mean([p['h_moyen'] for p in histogrammes])), 1),
        "s_moyen":     round(float(np.mean([p['s_moyen'] for p in histogrammes])), 1),
        "v_moyen":     round(float(np.mean([p['v_moyen'] for p in histogrammes])), 1),
        "hist_h":      [round(x, 4) for x in hist_moyen],
        "n_images":    len(histogrammes),
    }

    with open(_PROFILS_PATH, 'w', encoding='utf-8') as f:
        json.dump(profils, f, ensure_ascii=False, indent=2)

    global _PROFILS
    _PROFILS = profils
    print(f"✅ Équipe {nom} ajoutée avec {len(histogrammes)} image(s)")


if __name__ == '__main__':
    # Test rapide
    import sys
    profils = charger_profils()
    print(f"\n{len(profils)} équipes dans le dataset :")
    for cle, p in profils.items():
        print(f"  {p['drapeau']} {p['nom']:15} H={p['h_moyen']:.0f}° images={p['n_images']}")
