from pathlib import Path

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .config import settings
from .crud import (
    get_designs_by_tag,
    get_saved_designs_for_user,
    get_saved_tags_for_user,
    get_user_by_alias,
    remove_saved_design_for_user,
    serialize_design,
)
from .database import get_db
from .seed import seed_db
from .seed_data import TAG_LABELS

app = FastAPI(title=settings.app_name)
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.on_event("startup")
def startup_event():
    seed_db()


def render_gallery(request: Request, telegram_id: str, alias: str, tag: str | None, db: Session):
    return templates.TemplateResponse(
        "gallery.html",
        {
            "request": request,
            "designs": [serialize_design(item) for item in get_saved_designs_for_user(db, telegram_id, tag)],
            "tags": get_saved_tags_for_user(db, telegram_id),
            "tag_labels": TAG_LABELS,
            "active_tag": tag,
            "telegram_id": telegram_id,
            "alias": alias,
            "page_title": "Saved gallery",
        },
    )


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request, error: str | None = None, alias: str | None = None):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": error,
            "alias_value": alias or "",
            "page_title": "Open your gallery",
        },
    )


@app.get("/open-gallery")
def open_gallery(alias: str, db: Session = Depends(get_db)):
    user = get_user_by_alias(db, alias)
    if not user:
        return RedirectResponse(url=f"/?error=Alias not found&alias={alias}", status_code=302)
    clean_alias = (user.username or f"user{user.telegram_id}").lstrip("@")
    return RedirectResponse(url=f"/u/{clean_alias}", status_code=302)


@app.get("/u/{alias}", response_class=HTMLResponse)
def gallery_by_alias(request: Request, alias: str, tag: str | None = Query(default=None), db: Session = Depends(get_db)):
    user = get_user_by_alias(db, alias)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Alias not found",
                "alias_value": alias,
                "page_title": "Open your gallery",
            },
        )
    clean_alias = (user.username or f"user{user.telegram_id}").lstrip("@")
    return render_gallery(request, user.telegram_id, clean_alias, tag, db)


@app.get("/gallery/{telegram_id}", response_class=HTMLResponse)
def gallery_page(request: Request, telegram_id: str, tag: str | None = Query(default=None), db: Session = Depends(get_db)):
    user = get_user_by_alias(db, f"user{telegram_id}")
    alias = (user.username or f"user{telegram_id}").lstrip("@") if user else f"user{telegram_id}"
    return render_gallery(request, telegram_id, alias, tag, db)


@app.get("/api/by_tag/{tag}")
def api_by_tag(tag: str, db: Session = Depends(get_db)):
    return [serialize_design(item) for item in get_designs_by_tag(db, tag)]


@app.post("/api/remove/{telegram_id}/{design_id}")
def api_remove(telegram_id: str, design_id: int, db: Session = Depends(get_db)):
    return {"removed": remove_saved_design_for_user(db, telegram_id, design_id)}
