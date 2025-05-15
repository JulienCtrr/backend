from fastapi import FastAPI
from uuid import uuid4
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(CORSMiddleware,)
    allow_origins=["*", "https://localhost:8000"]

@app.get("/api/v1/{carte}/preinit")
async def preinit(carte: str):
    key = str(uuid4())

    res = JSONResponse({"key": key})
    res.set_cookie("key", key, httponly=True, samesite="none", maxe_age=3600)
    return res

@app.get("/api/v1/{carte}/init")
async def init(carte: str, carte = '1234'):
    query_key: str = Query(alias="key")
    query_cookie : str = Query(alias="key"), 

    return {}                       

ssd