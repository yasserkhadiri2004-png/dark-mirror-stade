API REST
========

GET /api/etat
-------------

Retourne l'etat detecte par la webcam (genre, equipe, couleur).

POST /api/voice
---------------

Body: `{ "texte": "Ou est mon parking ?" }`

Retourne la reponse textuelle et l'URL audio ElevenLabs.

GET /api/ticket/{code}
----------------------

Exemple: `/api/ticket/A215`

Retourne zone, rang, porte, parking, buvette, vestiaire.
