Installation
============

Prerequis
---------

* Python 3.10+
* Webcam
* Compte ElevenLabs (cle API)
* Compte Anthropic (optionnel)

Etapes
------

1. Cloner le repo::

    git clone https://github.com/yasserkhadiri2004-png/dark-mirror-stade.git
    cd dark-mirror-stade

2. Creer l'environnement virtuel::

    python -m venv .venv
    .venv\Scripts\activate

3. Installer les dependances::

    pip install flask opencv-python numpy requests
    pip install insightface onnxruntime deepface

4. Configurer la cle API dans tts_engine.py::

    API_KEY = "votre-cle-elevenlabs"

5. Lancer::

    python main.py

Ouvrez http://localhost:5000
