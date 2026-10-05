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
export SESSION_SECRET_KEY="$(openssl rand -hex 32)"
export COOKIE_SECURE=false
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000` and log in with username `admin` and password `admin`. This default is only for a private demo; anyone who can reach a public deployment can sign in with it. For a public deployment, set a unique `APP_PASSWORD` and a strong, random `SESSION_SECRET_KEY` in the deployment environment. Optionally set `APP_USERNAME` to change the username. Credentials are not displayed in the UI or stored in the repository. Login uses a browser-session cookie, and opening the app link directly prompts for login again; navigation through links inside the app keeps the current session. `COOKIE_SECURE=false` is only for local HTTP development; remove it or set it to `true` when serving the app over HTTPS. Use the same `SESSION_SECRET_KEY` across restarts so active sessions remain valid. The interactive API documentation at `/docs` also requires login.

The default username and password are both `admin`. Set `APP_USERNAME` and `APP_PASSWORD` before starting the app to override these demo defaults.

## Deploy to Railway

Create a Railway project from this repository and deploy it. `railway.json` selects the Dockerfile build and sets `/api/health` as the health check. The Docker image uses Python 3.12, installs only the web app dependencies, includes the static pages and CSV, and binds to Railway's `PORT` environment variable.

For public deployment, add a unique `APP_PASSWORD` and a strong, random `SESSION_SECRET_KEY` to Railway's service variables. Optionally set `APP_USERNAME`; it defaults to `admin`. The health-check endpoint remains public so Railway can monitor the service; application pages and data APIs require login. Do not leave the demo `admin` / `admin` credentials on a publicly accessible deployment.

Railway deploys the app; it does not install Python on a developer's computer. Locally, install Python with the operating system package manager first, then use `pip` to install Python packages.