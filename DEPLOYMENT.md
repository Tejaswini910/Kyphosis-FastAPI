# Kyphosis FastAPI app

The app has four pages: an overview dashboard (`/`), a filterable records table (`/records`), a prediction demo (`/prediction`), and project details (`/about`). Interactions use server-rendered HTML forms handled by Python/FastAPI; the UI does not use JavaScript. The prediction is an educational logistic-regression example trained on the included 81-record dataset. It is not clinically validated and must not be used for medical decisions.

## Run locally

Python is a runtime and cannot be installed with `pip`. This project targets Python 3.12. Python is already installed in Codespaces; on Ubuntu, install it with:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

From the repository root, install the app packages and start the server:

```bash
python3 -m pip install -r requirements-web.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`. Interactive API documentation is at `/docs`.

## Deploy to Railway

Create a Railway project from this repository and deploy it. `railway.json` selects the Dockerfile build and sets `/api/health` as the health check. The Docker image uses Python 3.12, installs only the web app dependencies, includes the static pages and CSV, and binds to Railway's `PORT` environment variable.

Railway deploys the app; it does not install Python on a developer's computer. Locally, install Python with the operating system package manager first, then use `pip` to install Python packages.