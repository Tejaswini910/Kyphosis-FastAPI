import csv
import hmac
import os
import secrets
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "FASTAP" / "kyphosis (1).csv"
STATIC_DIR = ROOT / "static"
templates = Jinja2Templates(directory=STATIC_DIR)

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY") or secrets.token_urlsafe(32)
APP_USERNAME = os.getenv("APP_USERNAME", "admin")


@asynccontextmanager
async def validate_auth_config(_app: FastAPI):
    if not os.getenv("APP_PASSWORD"):
        raise RuntimeError(
            "APP_PASSWORD must be set before starting the application. "
            "Set a strong password in the environment."
        )
    yield


app = FastAPI(
    title="Kyphosis Explorer",
    version="1.0.0",
    lifespan=validate_auth_config,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def require_login(request: Request, call_next):
    path = request.url.path
    public_paths = {"/login", "/api/health"}
    if (
        path not in public_paths
        and not path.startswith("/static/")
        and not request.session.get("authenticated")
    ):
        if path.startswith("/api/"):
            return JSONResponse({"detail": "Authentication required"}, status_code=401)
        return RedirectResponse(url="/login", status_code=303)
    return await call_next(request)


app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    same_site="lax",
    https_only=os.getenv("COOKIE_SECURE", "true").lower() == "true",
    max_age=8 * 60 * 60,
)


def csrf_token_for(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def valid_csrf_token(request: Request, submitted_token: str) -> bool:
    expected_token = request.session.pop("csrf_token", None)
    return bool(
        expected_token
        and hmac.compare_digest(expected_token, submitted_token)
    )


def credentials_match(username: str, password: str) -> bool:
    expected_password = os.getenv("APP_PASSWORD", "")
    username_matches = hmac.compare_digest(username, APP_USERNAME)
    password_matches = hmac.compare_digest(password, expected_password)
    return username_matches and password_matches


@lru_cache(maxsize=1)
def load_records() -> list[dict]:
    if not DATA_FILE.is_file():
        raise RuntimeError(f"Dataset not found: {DATA_FILE}")
    with DATA_FILE.open(newline="", encoding="utf-8-sig") as source:
        return [
            {
                "kyphosis": row["Kyphosis"].strip().lower(),
                "age": int(row["Age"]),
                "number": int(row["Number"]),
                "start": int(row["Start"]),
            }
            for row in csv.DictReader(source)
        ]


def render_page(request: Request, name: str, **context):
    return templates.TemplateResponse(
        request=request,
        name=name,
        context={
            "request": request,
            "csrf_token": csrf_token_for(request),
            "username": request.session.get("username", ""),
            **context,
        },
    )


@app.get("/login", include_in_schema=False)
def login_page(request: Request, error: Optional[str] = None):
    if request.session.get("authenticated"):
        return RedirectResponse(url="/", status_code=303)
    return render_page(
        request, "login.html", error=error, username_hint=APP_USERNAME
    )


@app.post("/login", include_in_schema=False)
def login(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    csrf_token: str = Form(),
):
    if not valid_csrf_token(request, csrf_token):
        return render_page(
            request,
            "login.html",
            error="Your session expired. Please try again.",
            username_hint=APP_USERNAME,
        )
    if not credentials_match(username, password):
        return render_page(
            request,
            "login.html",
            error="Invalid username or password.",
            username_hint=APP_USERNAME,
        )
    request.session.clear()
    request.session["authenticated"] = True
    request.session["username"] = username
    return RedirectResponse(url="/", status_code=303)


@app.post("/logout", include_in_schema=False)
def logout(request: Request, csrf_token: str = Form()):
    if not valid_csrf_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


def filtered_records(
    outcome: Optional[str], age_min: Optional[int], age_max: Optional[int]
) -> list[dict]:
    records = load_records()
    if outcome in {"present", "absent"}:
        records = [row for row in records if row["kyphosis"] == outcome]
    if age_min is not None:
        records = [row for row in records if row["age"] >= age_min]
    if age_max is not None:
        records = [row for row in records if row["age"] <= age_max]
    return records


def summarize(records: list[dict]) -> dict:
    total = len(records)
    present = [row for row in records if row["kyphosis"] == "present"]
    return {
        "total": total,
        "present": len(present),
        "absent": total - len(present),
        "present_rate": round(len(present) / total * 100, 1) if total else 0,
        "mean_age": round(sum(row["age"] for row in records) / total, 1) if total else 0,
        "mean_number": round(sum(row["number"] for row in records) / total, 1)
        if total
        else 0,
        "mean_start": round(sum(row["start"] for row in records) / total, 1)
        if total
        else 0,
        "present_mean_age": round(sum(row["age"] for row in present) / len(present), 1)
        if present
        else None,
    }


@app.get("/", include_in_schema=False)
def dashboard(
    request: Request,
    outcome: Optional[str] = Query(default=None),
    age_min: Optional[int] = Query(default=None, ge=0),
    age_max: Optional[int] = Query(default=None, ge=0),
):
    error = "Minimum age must not exceed maximum age." if age_min is not None and age_max is not None and age_min > age_max else None
    if error:
        age_min, age_max = None, None
    records = filtered_records(outcome, age_min, age_max)
    counts = [0] * 9
    for row in records:
        counts[min(row["age"] // 25, 8)] += 1
    max_count = max(counts, default=0) or 1
    age_bins = [
        {"label": f"{index * 25}+" if index == 8 else f"{index * 25}", "count": count,
         "height": round(count / max_count * 100)}
        for index, count in enumerate(counts)
    ]
    return render_page(
        request,
        "home-server.html",
        summary=summarize(records),
        age_bins=age_bins,
        outcome=outcome or "",
        age_min=age_min if age_min is not None else "",
        age_max=age_max if age_max is not None else "",
        error=error,
    )


@app.get("/records", include_in_schema=False)
def records_page(
    request: Request,
    outcome: Optional[str] = Query(default=None),
    age_min: Optional[int] = Query(default=None, ge=0),
    age_max: Optional[int] = Query(default=None, ge=0),
    sort: str = Query(default="age", pattern="^(age|number|start)$"),
    direction: str = Query(default="asc", pattern="^(asc|desc)$"),
):
    error = "Minimum age must not exceed maximum age." if age_min is not None and age_max is not None and age_min > age_max else None
    records = filtered_records(outcome, None if error else age_min, None if error else age_max)
    records.sort(key=lambda row: row[sort], reverse=direction == "desc")
    return render_page(
        request,
        "records-server.html",
        records=records,
        outcome=outcome or "",
        age_min=age_min if age_min is not None else "",
        age_max=age_max if age_max is not None else "",
        sort=sort,
        direction=direction,
        error=error,
    )


@app.get("/prediction", include_in_schema=False)
def prediction_page(request: Request):
    values = {"age": "80", "number": "4", "start": "10"}
    query = request.query_params
    prediction = None
    error = None
    if any(key in query for key in values):
        try:
            values = {key: query.get(key, "") for key in values}
            parsed = {key: int(value) for key, value in values.items()}
            data = PredictionInput(**parsed)
            prediction = predict(data)
        except (ValueError, TypeError) as exc:
            error = str(exc) or "Enter valid whole-number values for all three features."
        except HTTPException as exc:
            error = str(exc.detail)
    return render_page(
        request,
        "prediction-server.html",
        values=values,
        prediction=prediction,
        error=error,
    )


@app.get("/about", include_in_schema=False)
def about_page(request: Request):
    return render_page(request, "about-ui.html")


@app.get("/api/health", include_in_schema=False)
def health() -> dict:
    return {"status": "ok", "records": len(load_records())}


@app.get("/api/summary")
def summary() -> dict:
    records = load_records()
    present = [record for record in records if record["kyphosis"] == "present"]
    total = len(records)
    if not total:
        raise HTTPException(status_code=503, detail="Dataset is empty")
    return {
        "total": total,
        "present": len(present),
        "absent": total - len(present),
        "present_rate": round(len(present) / total * 100, 1),
        "mean_age": round(sum(row["age"] for row in records) / total, 1),
        "mean_number": round(sum(row["number"] for row in records) / total, 1),
        "mean_start": round(sum(row["start"] for row in records) / total, 1),
        "present_mean_age": round(sum(row["age"] for row in present) / len(present), 1)
        if present
        else None,
    }


@app.get("/api/records")
def get_records(
    outcome: Optional[str] = Query(default=None, pattern="^(present|absent)$"),
    age_min: Optional[int] = Query(default=None, ge=0),
    age_max: Optional[int] = Query(default=None, ge=0),
) -> dict:
    data = load_records()
    if age_min is not None and age_max is not None and age_min > age_max:
        raise HTTPException(status_code=422, detail="age_min must not exceed age_max")
    if outcome:
        data = [record for record in data if record["kyphosis"] == outcome]
    if age_min is not None:
        data = [record for record in data if record["age"] >= age_min]
    if age_max is not None:
        data = [record for record in data if record["age"] <= age_max]
    return {"count": len(data), "records": data}


class PredictionInput(BaseModel):
    age: int = Field(ge=0, le=250)
    number: int = Field(ge=1, le=20)
    start: int = Field(ge=1, le=30)


@lru_cache(maxsize=1)
def prediction_model():
    records = load_records()
    features = [[row["age"], row["number"], row["start"]] for row in records]
    labels = [row["kyphosis"] for row in records]
    return make_pipeline(
        StandardScaler(), LogisticRegression(max_iter=1000, random_state=42)
    ).fit(features, labels)


@app.post("/api/predict")
def predict(data: PredictionInput) -> dict:
    model = prediction_model()
    features = [[data.age, data.number, data.start]]
    probabilities = model.predict_proba(features)[0]
    classes = list(model.classes_)
    present_probability = float(probabilities[classes.index("present")])
    return {
        "prediction": str(model.predict(features)[0]),
        "present_probability": round(present_probability * 100, 1),
        "model": "Logistic regression trained on the full 81-record dataset",
        "warning": "Educational demonstration only. Not validated for clinical use or individual medical decisions.",
    }