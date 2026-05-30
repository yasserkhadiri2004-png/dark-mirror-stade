import cv2
import numpy as np

VISAGE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
YEUX   = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
SOURIRE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

MAILLOTS = {
    'rouge':  ([0,   120, 70],  [10,  255, 255]),
    'rouge2': ([170, 120, 70],  [180, 255, 255]),
    'vert':   ([40,  80,  40],  [80,  255, 255]),
    'bleu':   ([100, 80,  40],  [130, 255, 255]),
    'blanc':  ([0,   0,   200], [180, 30,  255]),
    'noir':   ([0,   0,   0],   [180, 255, 50 ]),
    'jaune':  ([20,  100, 100], [40,  255, 255]),
}

genre_detecte   = None
couleur_maillot = None

def estimer_genre(visage_img):
    h, w = visage_img.shape[:2]
    ratio = w / h if h > 0 else 1
    gris  = cv2.cvtColor(visage_img, cv2.COLOR_BGR2GRAY)

    yeux    = YEUX.detectMultiScale(gris, 1.1, 5, minSize=(15, 15))
    sourires = SOURIRE.detectMultiScale(gris, 1.7, 20)

    score_homme = 0
    score_femme = 0

    if ratio > 0.88:
        score_homme += 2
    else:
        score_femme += 2

    if len(sourires) > 0:
        score_femme += 1
    else:
        score_homme += 1

    if len(yeux) >= 2:
        score_femme += 1

    return 'homme' if score_homme >= score_femme else 'femme'

import cv2
import numpy as np
import json

# ── Charger les équipes ──────────────────────────
with open('data/equipes.json', 'r', encoding='utf-8') as f:
    EQUIPES = json.load(f)

VISAGE  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
YEUX    = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
SOURIRE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

genre_detecte   = None
couleur_maillot = None
equipe_detectee = None

def detecter_equipe(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, w = hsv.shape[:2]
    roi  = hsv[h//4 : 3*h//4, w//4 : 3*w//4]

    meilleure_equipe = None
    meilleur_score   = 0

    for nom_equipe, data in EQUIPES.items():
        score_total = 0
        for type_couleur, (low, high) in data['couleurs_hsv'].items():
            masque = cv2.inRange(roi, np.array(low), np.array(high))
            score  = cv2.countNonZero(masque)
            score_total += score

        if score_total > meilleur_score:
            meilleur_score   = score_total
            meilleure_equipe = nom_equipe

    if meilleur_score < 800:
        return None
    return meilleure_equipe

def estimer_genre(visage_img):
    h, w  = visage_img.shape[:2]
    ratio = w / h if h > 0 else 1
    gris  = cv2.cvtColor(visage_img, cv2.COLOR_BGR2GRAY)

    sourires = SOURIRE.detectMultiScale(gris, 1.7, 20)
    yeux     = YEUX.detectMultiScale(gris, 1.1, 5, minSize=(15,15))

    score_homme = 2 if ratio > 0.88 else 0
    score_femme = 0 if ratio > 0.88 else 2
    score_femme += 1 if len(sourires) > 0 else 0
    score_homme += 0 if len(sourires) > 0 else 1
    score_femme += 1 if len(yeux) >= 2 else 0

    return 'homme' if score_homme >= score_femme else 'femme'

def lancer_camera():
    global genre_detecte, couleur_maillot, equipe_detectee

    cap = cv2.VideoCapture(0)
    print("Webcam lancee - Q pour quitter")

    while True:
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.flip(frame, 1)

        # Détection équipe
        equipe = detecter_equipe(frame)
        if equipe:
            equipe_detectee = equipe
            couleur_maillot = EQUIPES[equipe]['couleur_hex']

        # Détection genre
        gris    = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        visages = VISAGE.detectMultiScale(gris, 1.1, 5, minSize=(80,80))
        for (x,y,w,h) in visages:
            genre_detecte = estimer_genre(frame[y:y+h, x:x+w])
            couleur_box   = (255,150,50) if genre_detecte=='homme' else (220,100,255)
            cv2.rectangle(frame, (x,y), (x+w,y+h), couleur_box, 2)
            cv2.putText(frame, genre_detecte, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, couleur_box, 2)

        # Affichage
        if equipe_detectee:
            info = EQUIPES[equipe_detectee]
            label = f"{info['drapeau']} {info['nom']} — {info['surnom']}"
        else:
            label = "Aucune equipe detectee"

        cv2.putText(frame, label, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

        # Rectangle zone analyse
        fh, fw = frame.shape[:2]
        cv2.rectangle(frame, (fw//4,fh//4), (3*fw//4,3*fh//4), (0,200,0), 1)

        cv2.imshow("Dark Mirror - Camera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return {'genre': genre_detecte, 'equipe': equipe_detectee}

if __name__ == '__main__':
    print(lancer_camera())

def lancer_camera():
    global genre_detecte, couleur_maillot

    cap = cv2.VideoCapture(0)
    print("Webcam lancee - Appuyez sur Q pour quitter")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Correction effet miroir
        frame = cv2.flip(frame, 1)

        gris   = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        visages = VISAGE.detectMultiScale(gris, 1.1, 5, minSize=(80, 80))

        # Detection couleur maillot
        couleur_maillot = detecter_couleur(frame)

        # Detection genre sur chaque visage
        for (x, y, w, h) in visages:
            visage_img    = frame[y:y+h, x:x+w]
            genre_detecte = estimer_genre(visage_img)

            couleur_box = (255, 150, 50) if genre_detecte == 'homme' else (220, 100, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), couleur_box, 2)
            cv2.putText(frame, genre_detecte, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, couleur_box, 2)

        # Affichage texte
        label_g = f"Genre  : {genre_detecte}" if genre_detecte else "Genre  : en attente..."
        label_m = f"Maillot: {couleur_maillot}" if couleur_maillot else "Maillot: aucun"

        cv2.putText(frame, label_g, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        cv2.putText(frame, label_m, (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255,   0), 2)

        # Rectangle zone analyse maillot
        fh, fw = frame.shape[:2]
        cv2.rectangle(frame,
                      (fw//4, fh//4),
                      (3*fw//4, 3*fh//4),
                      (0, 200, 0), 1)
        cv2.putText(frame, "Zone maillot", (fw//4 + 5, fh//4 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)

        cv2.imshow("Dark Mirror - Camera", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return {'genre': genre_detecte, 'maillot': couleur_maillot}

if __name__ == '__main__':
    res = lancer_camera()
    print(f"\nResultat final : {res}")