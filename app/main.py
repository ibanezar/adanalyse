from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.db import init_db
from app.routes import analyze, generate, report, upload

app = FastAPI(title="Winning Ads Analyzer")

templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(report.router)
app.include_router(generate.router)


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "upload.html")
