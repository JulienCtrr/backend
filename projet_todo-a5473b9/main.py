from contextlib import asynccontextmanager
from typing import Annotated
from databases import Database
from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Static files are handled by a specific sub-router 
static = StaticFiles(directory="static")

# We instanciate a template engine for jinja2
templates = Jinja2Templates(directory="templates")

# The database connection
database = Database('sqlite+aiosqlite:///data.db')

# Connect/disconnect the database when the app starts/stops
@asynccontextmanager
async def lifespan(_app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

# We mount the static files handler under /static
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, filter: Annotated[str, Query()] = "all"):
    query = "SELECT * FROM Todos" 
    if filter == "active":
        query += " WHERE is_done = 0"
    elif filter == "completed":
        query += " WHERE is_done = 1"
    query += " ORDER BY created_at DESC"
    todos = await database.fetch_all(query)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "todos": todos,
        }
    )

@app.post("/todos")
async def create_todo(content: Annotated[str, Form()]):
    await database.execute(
        "INSERT INTO Todos (content) VALUES (:content)", 
        { "content": content }
    )
    return RedirectResponse(url="/", status_code=303)

@app.post("/todos/{todo_id}")
async def update_todos(todo_id: int, 
                       is_done: Annotated[bool, Form()], 
                       action: Annotated[str, Form()]):
    if action == "update":
        await database.execute(
            "UPDATE Todos SET is_done = :is_done WHERE id = :todo_id",
            {"todo_id": todo_id, "is_done": is_done}
        )
    else:
        await database.execute(
            "DELETE FROM Todos WHERE id = :todo_id",
            {"todo_id": todo_id}
        )
    return RedirectResponse(url="/", status_code=303)

