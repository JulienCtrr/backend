from copy import deepcopy
import time
from uuid import uuid4
from fastapi import FastAPI, Cookie, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://localhost:8000"],
    allow_credentials=True
)

class UserInfo:
    def __init__(self, carte):
        self.last_seen_map = deepcopy(carte)
        self.last_edited_time_nanos = 0

class Carte:
    def __init__(self, nx: int, ny: int, timeout_nanos: int = 10e9):
        self.keys = set()
        self.nx = nx 
        self.ny = ny
        self.data = [
            [(0,0,0) for _ in range(ny)]
            for _ in range(nx)
        ]
        self.timeout_nanos = timeout_nanos
        self.users: dict[str, UserInfo] = {}

    def create_new_key(self):
        key = str(uuid4())
        self.keys.add(key)
        return key
    
    def is_valid_key(self, key: str):
        return key in self.keys
    
    def create_new_user_id(self):
        user_id = str(uuid4())
        self.users[user_id] = UserInfo(self.data)
        return user_id
    
    def is_valid_user_id(self, user_id: str):
        return user_id in self.users
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int, user_id: str):
        if not self.is_valid_user_id(user_id):
            return {"error": "ID utilisateur invalide"}
        now = time.time_ns()
        user_info = self.users[user_id]
        if now - user_info.last_edited_time_nanos < self.timeout_nanos:
            wait_s = int((self.timeout_nanos - (now - user_info.last_edited_time_nanos))/1e9)
            return {"error": f"Attends {wait_s} s avant de remettre un pixel"}
        self.data[x][y] = (r, g, b)
        user_info.last_edited_time_nanos = now
        return {"status": "ok", "x": x, "y": y, "color": (r, g, b)}

# Dictionnaire global des cartes
cartes: dict[str, Carte] = {"1234": Carte(10, 10)}

@app.get("/api/v1/{carte}/preinit")
async def preinit(carte: str):
    if carte not in cartes:
        return {"error": "Carte inconnue"}

    key = cartes[carte].create_new_key()
    res = JSONResponse({"key": key})
    res.set_cookie("key", key, httponly=True, samesite="none", secure=True, max_age=3600)
    return res

@app.get("/api/v1/{carte}/init")
async def init(
    carte: str,
    query_key: str = Query(alias="key"),
    cookie_key: str = Cookie(alias="key")
):
    if carte not in cartes:
        return {"error": "Carte inconnue"}
    
    c = cartes[carte]

    if query_key != cookie_key:
        return {"error": "Les clés ne correspondent pas"}
    
    if not c.is_valid_key(cookie_key):
        return {"error": "Clé invalide"}

    user_id = c.create_new_user_id()
    res = JSONResponse({
        "id": user_id,
        "nx": c.nx,
        "ny": c.ny,
        "data": c.data
    })
    res.set_cookie("id", user_id, httponly=True, samesite="none", secure=True, max_age=3600)
    return res

@app.get("/api/v1/{carte}/deltas")
async def deltas(
    carte: str,
    query_user_id: str = Query(alias="id"),
    cookie_key: str = Cookie(alias="key"),
    cookie_user_id: str = Cookie(alias="id")
):
    if carte not in cartes:
        return {"error": "Carte inconnue"}
    
    c = cartes[carte]

    if not c.is_valid_key(cookie_key):
        return {"error": "Clé invalide"}
    
    if query_user_id != cookie_user_id:
        return {"error": "Les identifiants ne correspondent pas"}
    
    if not c.is_valid_user_id(query_user_id):
        return {"error": "Utilisateur inconnu"}

    user_info = c.users[query_user_id]
    user_carte = user_info.last_seen_map

    deltas: list[tuple[int,int,int,int,int]] = []
    for y in range(c.ny):
        for x in range(c.nx):
            if c.data[x][y] != user_carte[x][y]:
                deltas.append((x, y, *c.data[x][y]))
    
    user_info.last_seen_map = deepcopy(c.data)

    return {
        "id": query_user_id,
        "nx": c.nx,
        "ny": c.ny,
        "deltas": deltas
    }

@app.post("/api/v1/{carte}/set_pixel")
async def set_pixel(
    carte: str,
    x: int = Query(...),
    y: int = Query(...),
    r: int = Query(...),
    g: int = Query(...),
    b: int = Query(...),
    cookie_key: str = Cookie(alias="key"),
    cookie_user_id: str = Cookie(alias="id")
):
    if carte not in cartes:
        return {"error": "Carte inconnue"}

    c = cartes[carte]

    if not c.is_valid_key(cookie_key):
        return {"error": "Clé invalide"}
    
    if not c.is_valid_user_id(cookie_user_id):
        return {"error": "ID utilisateur invalide"}
    
    if not (0 <= x < c.nx and 0 <= y < c.ny):
        return {"error": "Coordonnées invalides"}
    
    result = c.set_pixel(x, y, r, g, b, cookie_user_id)
    if "error" in result:
        return {"error": result["error"]}
    
    return result
