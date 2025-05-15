from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À adapter selon vos besoins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Liste de mots de 5 lettres
mots = ["ARBRE", "MAISON", "CHIEN", "TABLE", "FLEUR", "LIVRE", "PORTE", "CHAIR", "VITES", "GLACE"]

# Mot secret actuel
mot_secret = ""

@app.get("/api/v1/wordle/new")
async def nouvelle_partie():
    global mot_secret
    mot_secret = random.choice(mots)
    return {"message": "Nouvelle partie commencée."}

@app.get("/api/v1/wordle/guess")
async def verifier_mot(mot: str = Query(..., min_length=5, max_length=5)):
    global mot_secret
    mot = mot.upper()
    if not mot_secret:
        return JSONResponse(status_code=400, content={"error": "Aucune partie en cours. Veuillez démarrer une nouvelle partie."})

    resultat = []
    mot_temp = list(mot_secret)  # Pour marquer les lettres déjà utilisées

    # Première passe : lettres bien placées
    for i in range(5):
        if mot[i] == mot_secret[i]:
            resultat.append({"lettre": mot[i], "couleur": "green"})
            mot_temp[i] = None  # Marquer la lettre comme utilisée
        else:
            resultat.append({"lettre": mot[i], "couleur": "grey"})

    # Deuxième passe : lettres mal placées
    for i in range(5):
        if resultat[i]["couleur"] == "grey" and mot[i] in mot_temp:
            resultat[i]["couleur"] = "yellow"
            mot_temp[mot_temp.index(mot[i])] = None  # Marquer la lettre comme utilisée

    return {"correct": resultat}
