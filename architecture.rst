Architecture
============

Flux de detection
-----------------

.. code-block:: text

    Webcam
      |
    OpenCV DNN  ->  Detection visage (confiance > 0.6)
      |
    InsightFace ->  Genre (3 votes -> arret definitif)
      |
    HSV Hist    ->  Equipe supportee
      |
    Flask /api/etat -> Three.js Avatar 3D

Flux assistant vocal
--------------------

.. code-block:: text

    Visiteur clique micro
      |
    Web Speech API -> Transcription fr-FR
      |
    Flask /api/voice -> Claude Haiku
      |
    ElevenLabs -> MP3 -> Avatar talking

Composants
----------

+----------------------+------------------------------------------+
| Fichier              | Role                                     |
+======================+==========================================+
| main.py              | Serveur Flask + thread webcam            |
+----------------------+------------------------------------------+
| voice_assistant.py   | Assistant vocal + RAG Google Maps        |
+----------------------+------------------------------------------+
| tts_engine.py        | Moteur ElevenLabs TTS                    |
+----------------------+------------------------------------------+
| gender_detector.py   | Detection genre InsightFace              |
+----------------------+------------------------------------------+
| detector_maillot.py  | Detection equipe par histogrammes        |
+----------------------+------------------------------------------+
| web/index.html       | Interface Dark Mirror Three.js           |
+----------------------+------------------------------------------+
