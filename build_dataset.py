"""
build_dataset.py — Télécharge automatiquement des images de maillots
et construit les profils de couleur HSV pour chaque équipe.

Usage :
    python build_dataset.py
    → crée data/maillots_profiles.json
"""

import cv2
import numpy as np
import json
import os
import urllib.request
import time

os.makedirs("data/maillots", exist_ok=True)

# ── URLs d'images de maillots par équipe ─────────────────────────────────────
# Images Wikipedia (domaine public / licence libre)
EQUIPES_URLS = {
    "maroc": {
        "nom": "Maroc", "surnom": "Lions de l'Atlas", "drapeau": "🇲🇦",
        "couleur_hex": "#C1272D",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Morocco_2022_FIFA_World_Cup_home_kit.png/200px-Morocco_2022_FIFA_World_Cup_home_kit.png",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Morocco_national_football_team_2022.jpg/320px-Morocco_national_football_team_2022.jpg",
        ]
    },
    "france": {
        "nom": "France", "surnom": "Les Bleus", "drapeau": "🇫🇷",
        "couleur_hex": "#002395",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/France_national_football_team_2022_FIFA_World_Cup.jpg/320px-France_national_football_team_2022_FIFA_World_Cup.jpg",
        ]
    },
    "allemagne": {
        "nom": "Allemagne", "surnom": "Die Mannschaft", "drapeau": "🇩🇪",
        "couleur_hex": "#FFFFFF",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Germany_national_football_team_2014_FIFA_World_Cup.jpg/320px-Germany_national_football_team_2014_FIFA_World_Cup.jpg",
        ]
    },
    "bresil": {
        "nom": "Brésil", "surnom": "La Seleção", "drapeau": "🇧🇷",
        "couleur_hex": "#FDD116",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Brazil_national_football_team_2022_FIFA_World_Cup.jpg/320px-Brazil_national_football_team_2022_FIFA_World_Cup.jpg",
        ]
    },
    "espagne": {
        "nom": "Espagne", "surnom": "La Roja", "drapeau": "🇪🇸",
        "couleur_hex": "#AA151B",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Spain_national_football_team_2022_FIFA_World_Cup.jpg/320px-Spain_national_football_team_2022_FIFA_World_Cup.jpg",
        ]
    },
    "argentine": {
        "nom": "Argentine", "surnom": "L'Albiceleste", "drapeau": "🇦🇷",
        "couleur_hex": "#74ACDF",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Argentina_national_football_team_2022_FIFA_World_Cup.jpg/320px-Argentina_national_football_team_2022_FIFA_World_Cup.jpg",
        ]
    },
    "portugal": {
        "nom": "Portugal", "surnom": "A Seleção", "drapeau": "🇵🇹",
        "couleur_hex": "#006600",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Portugal_national_football_team_2022_FIFA_World_Cup.jpg/320px-Portugal_national_football_team_2022_FIFA_World_Cup.jpg",
        ]
    },
    "angleterre": {
        "nom": "Angleterre", "surnom": "Three Lions", "drapeau": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "couleur_hex": "#FFFFFF",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d9/England_national_football_team_2022_FIFA_World_Cup.jpg/320px-England_national_football_team_2022_FIFA_World_Cup.jpg",
        ]
    },
    "senegal": {
        "nom": "Sénégal", "surnom": "Lions de la Téranga", "drapeau": "🇸🇳",
        "couleur_hex": "#00853F",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fd/Senegal_national_football_team_2022_FIFA_World_Cup.jpg/320px-Senegal_national_football_team_2022_FIFA_World_Cup.jpg",
        ]
    },
    "nigeria": {
        "nom": "Nigeria", "surnom": "Super Eagles", "drapeau": "🇳🇬",
        "couleur_hex": "#008751",
        "urls": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Nigeria_national_football_team.jpg/320px-Nigeria_national_football_team.jpg",
        ]
    },
}

def extraire_profil_hsv(image_path: str) -> dict | None:
    """
    Extrait le profil HSV dominant d'une image de maillot.
    Analyse uniquement la zone centrale (torse) pour éviter le fond.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None

    h, w = img.shape[:2]

    # Zone torse : centre de l'image, 40% de la largeur, 50% de la hauteur
    y1 = int(h * 0.25)
    y2 = int(h * 0.75)
    x1 = int(w * 0.30)
    x2 = int(w * 0.70)
    roi = img[y1:y2, x1:x2]

    if roi.size == 0:
        return None

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Masque pour éliminer les pixels très sombres (ombre/fond) et très clairs (fond blanc)
    masque = cv2.inRange(hsv,
        np.array([0,  20,  30]),
        np.array([180, 255, 240])
    )

    pixels_valides = hsv[masque > 0]
    if len(pixels_valides) < 100:
        return None

    # Calculer histogramme H (teinte) sur 18 bins
    hist_h = cv2.calcHist([hsv], [0], masque, [18], [0, 180])
    hist_h = hist_h.flatten() / hist_h.sum()

    # Couleur dominante
    h_moyen = float(np.average(np.arange(18) * 10, weights=hist_h))
    s_moyen = float(np.mean(pixels_valides[:, 1]))
    v_moyen = float(np.mean(pixels_valides[:, 2]))

    return {
        "h_moyen":   round(h_moyen, 1),
        "s_moyen":   round(s_moyen, 1),
        "v_moyen":   round(v_moyen, 1),
        "hist_h":    [round(float(x), 4) for x in hist_h],
    }


def telecharger_image(url: str, chemin: str) -> bool:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            with open(chemin, 'wb') as f:
                f.write(r.read())
        return True
    except Exception as e:
        print(f"    ✗ Erreur téléchargement : {e}")
        return False


def construire_profils():
    print("=" * 55)
    print("  Construction des profils de maillots")
    print("=" * 55)

    profils = {}

    for cle, data in EQUIPES_URLS.items():
        print(f"\n{data['drapeau']} {data['nom']}...")
        histogrammes = []

        for i, url in enumerate(data['urls']):
            chemin = f"data/maillots/{cle}_{i}.jpg"

            # Télécharger si pas déjà là
            if not os.path.exists(chemin):
                print(f"  Téléchargement image {i+1}...")
                if not telecharger_image(url, chemin):
                    continue
                time.sleep(0.5)

            profil = extraire_profil_hsv(chemin)
            if profil:
                histogrammes.append(profil)
                print(f"  ✔ Image {i+1} : H={profil['h_moyen']:.0f}° S={profil['s_moyen']:.0f} V={profil['v_moyen']:.0f}")

        if histogrammes:
            # Moyenne des histogrammes
            hist_moyen = np.mean([p['hist_h'] for p in histogrammes], axis=0).tolist()
            profils[cle] = {
                "nom":         data['nom'],
                "surnom":      data['surnom'],
                "drapeau":     data['drapeau'],
                "couleur_hex": data['couleur_hex'],
                "h_moyen":     round(float(np.mean([p['h_moyen'] for p in histogrammes])), 1),
                "s_moyen":     round(float(np.mean([p['s_moyen'] for p in histogrammes])), 1),
                "v_moyen":     round(float(np.mean([p['v_moyen'] for p in histogrammes])), 1),
                "hist_h":      [round(x, 4) for x in hist_moyen],
                "n_images":    len(histogrammes),
            }
            print(f"  → Profil construit ({len(histogrammes)} image(s))")
        else:
            print(f"  ✗ Aucune image valide")

    chemin_json = "data/maillots_profiles.json"
    with open(chemin_json, 'w', encoding='utf-8') as f:
        json.dump(profils, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(profils)} profils sauvegardés → {chemin_json}")
    return profils


if __name__ == '__main__':
    construire_profils()
