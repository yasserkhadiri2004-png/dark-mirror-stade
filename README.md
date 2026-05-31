# 🏟️ Dark Mirror — Assistant IA Stade Moulay Abdellah

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-green?logo=flask)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-red?logo=opencv)
![Three.js](https://img.shields.io/badge/Three.js-r153-black?logo=threedotjs)
![ElevenLabs](https://img.shields.io/badge/ElevenLabs-TTS-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Assistant virtuel intelligent pour l'accueil des visiteurs au Stade Moulay Abdellah de Rabat**

[Démo](#démo) • [Installation](#installation) • [Technologies](#technologies) • [Fonctionnalités](#fonctionnalités) • [Architecture](#architecture)

</div>

---

## 📸 Aperçu

Dark Mirror est un kiosque d'accueil intelligent qui :
- 👁️ **Détecte le visiteur** via webcam (genre + équipe supportée)
- 🤖 **Affiche un avatar 3D** animé qui s'adapte au genre détecté
- 🎤 **Répond aux questions** oralement en français via IA
- 🎫 **Valide les tickets** et annonce les informations de place
- 🗺️ **Guide vers les services** autour du stade (hôtels, restaurants, transports)

---

## ✨ Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| 👤 Détection de genre | InsightFace (92%+ précision) — 3 votes puis arrêt |
| 👕 Détection d'équipe | Histogrammes HSV + profils de vrais maillots |
| 🤖 Avatar 3D | Three.js + GLB/Mixamo — animations idle/wave/point/happy/talking |
| 🎤 Assistant vocal | Web Speech API → Claude Haiku → ElevenLabs TTS |
| 🎫 Validation ticket | QR code + saisie manuelle — annonce vocale complète |
| 🗺️ RAG services | Google Maps API — hôtels, restaurants, transports autour du stade |
| 🌐 Interface Dark | Style cyber noir/bleu · Three.js · particules · responsive |

---

## 🛠️ Technologies

```
Vision IA          OpenCV DNN + InsightFace + DeepFace
Détection maillot  Histogrammes HSV + Google Maps dataset
Avatar 3D          Three.js r153 + GLTFLoader + Mixamo animations
IA conversationnelle  Anthropic Claude Haiku (claude-haiku-4-5)
Synthèse vocale    ElevenLabs eleven_multilingual_v2
Reconnaissance vocale  Web Speech API (fr-FR)
RAG                Google Places API + recherche par histogramme
Backend            Flask + threading
Frontend           Vanilla JS + Three.js · style Dark Mirror
```

---

## 📁 Structure du projet

```
Projet_computer_vision/
├── main.py                 # Serveur Flask + thread webcam
├── voice_assistant.py      # Assistant vocal + RAG
├── tts_engine.py           # Moteur ElevenLabs TTS
├── gender_detector.py      # Détection genre InsightFace
├── detector_maillot.py     # Détection équipe par histogrammes
├── build_dataset.py        # Construction dataset maillots (Google Maps)
├── camera.py               # Détection webcam standalone
├── ticket.py               # Validation tickets QR + manuelle
├── liste_voix.py           # Utilitaire découverte voix ElevenLabs
│
├── data/
│   ├── equipes.json        # 9 équipes africaines + mondiales
│   ├── tickets.json        # Base de tickets
│   └── maillots_profiles.json  # Profils HSV des maillots
│
├── web/
│   └── index.html          # Interface Dark Mirror (Three.js)
│
└── static/
    ├── avatar_homme_idle.glb   # Avatar masculin — animations
    ├── avatar_homme_wave.glb
    ├── avatar_homme_point.glb
    ├── avatar_homme_happy.glb
    ├── avatar_homme_talking.glb
    ├── avatar_femme_idle.glb   # Avatar féminin — animations
    └── sounds/                 # Fichiers audio TTS générés
```

---

## ⚡ Installation

### Prérequis
- Python 3.10+
- Webcam
- Compte ElevenLabs (clé API)
- Compte Anthropic (clé API) — optionnel

### 1. Cloner le repo

```bash
git clone https://github.com/VOTRE_USERNAME/dark-mirror-stade.git
cd dark-mirror-stade
```

### 2. Créer l'environnement virtuel

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac
```

### 3. Installer les dépendances

```bash
pip install flask opencv-python numpy requests insightface onnxruntime
pip install deepface elevenlabs pyzbar
```

### 4. Configurer les clés API

Créez un fichier `.env` à la racine :

```env
ANTHROPIC_API_KEY=sk-ant-votre-cle-ici
OPENAI_API_KEY=sk-votre-cle-ici        # Optionnel (Whisper)
```

Ou modifiez directement dans `tts_engine.py` :

```python
API_KEY = "votre-cle-elevenlabs"
```

### 5. Construire le dataset maillots (optionnel)

```bash
python build_dataset.py --key VOTRE_CLE_GOOGLE_MAPS
```

### 6. Lancer

```bash
python main.py
```

Ouvrez **http://localhost:5000** — mettez-vous devant la webcam !

---

## 🎭 Avatars

Les avatars 3D proviennent de **Mixamo (Adobe)** avec les animations :
- `idle` — respiration naturelle (boucle)
- `wave` — salutation à l'arrivée
- `point` — indication de direction (ticket)
- `happy` — applaudissement (sourire détecté)
- `talking` — lèvres animées (ElevenLabs parle)

Placez vos fichiers `.glb` dans `static/` avec les noms exacts :
```
avatar_homme_idle.glb · avatar_homme_wave.glb · avatar_homme_point.glb
avatar_homme_happy.glb · avatar_homme_talking.glb
avatar_femme_idle.glb · avatar_femme_wave.glb · ...
```

---

## 🏗️ Architecture

```
Webcam
  ↓
OpenCV DNN → Détection visage
  ↓
InsightFace → Genre (3 votes → arrêt)
  ↓
HSV Histogramme → Équipe supportée
  ↓
Flask API /api/etat
  ↓
Three.js → Avatar 3D (genre adapté + animations)

Visiteur clique 🎤
  ↓
Web Speech API → Transcription fr-FR
  ↓
Flask /api/voice → Claude Haiku
  ↓
ElevenLabs → MP3 → Avatar talking
```

---

## 🗺️ Roadmap

- [x] Détection genre + équipe
- [x] Avatar 3D animé
- [x] Assistant vocal ElevenLabs
- [x] Validation ticket QR
- [x] RAG Google Maps


---



---

## 👤 Auteur

**Yasser KHADIRI** — Étudiant ENSAM Meknès  
📧 yasserkhadiri2004@gmail.com

---

## 📄 Licence

MIT License — libre d'utilisation avec attribution.

---

<div align="center">
  <strong>🇲🇦 Stade Moulay Abdellah · Rabat · Maroc</strong><br>
  <em>Projet réalisé dans le cadre de la Coupe du Monde 2030</em>
</div>
