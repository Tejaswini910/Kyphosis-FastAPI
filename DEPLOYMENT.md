# Kyphosis FastAPI app

The app has four pages: an overview dashboard (`/`), a filterable records table (`/records`), a prediction demo (`/prediction`), and project details (`/about`). Interactions use server-rendered HTML forms handled by Python/FastAPI; the UI does not use JavaScript. The prediction is an educational logistic-regression example trained on the included 81-record dataset. It is not clinically validated and must not be used for medical decisions.

## Run locally

Python is a runtime and cannot be installed with `pip`. This project targets Python 3.12. Python is already installed in Codespaces; on Ubuntu, install it with:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

From the repository root, install the app packages, configure the single application account, and start the server:

```bash
python3 -m pip install -r requirements-web.txt
export APP_USERNAME=admin
export APP_PASSWORD='replace-with-a-long-unique-password'
export SESSION_SECRET_KEY="$(openssl rand -hex 32)"
export COOKIE_SECURE=false
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`. The app redirects unauthenticated visitors to its login page. Set a strong password and keep it private; credentials are not displayed in the UI or stored in the repository. `COOKIE_SECURE=false` is only for local HTTP development; remove it or set it to `true` when serving the app over HTTPS. Use the same `SESSION_SECRET_KEY` across restarts so active sessions remain valid. The interactive API documentation at `/docs` also requires login.

The default username is `admin`. To change it, set `APP_USERNAME` before starting the app. Set `APP_PASSWORD` and `SESSION_SECRET_KEY` in your deployment provider's secret/environment-variable settings, not in committed files.

## Deploy to Railway

Create a Railway project from this repository and deploy it. `railway.json` selects the Dockerfile build and sets `/api/health` as the health check. The Docker image uses Python 3.12, installs only the web app dependencies, includes the static pages and CSV, and binds to Railway's `PORT` environment variable.

Before deployment, add `APP_PASSWORD` and a strong, random `SESSION_SECRET_KEY` to Railway's service variables. Optionally set `APP_USERNAME`; it defaults to `admin`. The health-check endpoint remains public so Railway can monitor the service; application pages and data APIs require login.

Railway deploys the app; it does not install Python on a developer's computer. Locally, install Python with the operating system package manager first, then use `pip` to install Python packages.