API REST
========

GET /api/etat
-------------

Retourne l'etat detecte par la webcam.

**Reponse** ::

    {
      "genre":    "homme" | "femme" | null,
      "maillot":  "Maroc" | null,
      "equipe":   "maroc" | null,
      "drapeau":  "MA" | null,
      "surnom":   "Lions de l'Atlas" | null,
      "couleur":  "#C1272D" | null,
      "souriant": false
    }

POST /api/voice
---------------

Envoie une question a l'assistant vocal.

**Body JSON** ::

    { "texte": "Ou est mon parking ?" }

**Reponse** ::

    {
      "question":  "Ou est mon parking ?",
      "texte":     "Votre parking est cote Nord...",
      "audio_url": "/static/sounds/tts_xxx.mp3"
    }

GET /api/ticket/{code}
----------------------

Valide un ticket et retourne les informations.

**Exemple** : ``GET /api/ticket/A215``

**Reponse** ::

    {
      "zone":      "Tribune Nord - Bloc A",
      "rang":      "Rang 2, Siege 15",
      "porte":     "Entree 1 - Cote Nord",
      "parking":   "Parking Nord P1",
      "buvette":   "Buvette N1",
      "vestiaire": "Vestiaire A - Niveau 0"
    }

GET /api/equipes
----------------

Retourne la liste de toutes les equipes configurees.
