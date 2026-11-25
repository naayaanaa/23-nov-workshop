# Campus Connect API and frontend

This repository includes the Flask API, the frontend source and design references in `frontend/`, and a deployable frontend copy in `public/`. Vercel serves `public/` from its CDN and Flask handles the `/api/...` routes on the same domain.

## Deploy to Vercel

1. Import this Git repository and use its root directory (the folder containing `app.py`).
2. Let Vercel detect the **Flask** framework. Leave the build and output directory fields empty.
3. Add `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` as Vercel environment variables for Preview and Production. Do not commit `.env`; Vercel gets these values from its project settings.
4. Deploy. Vercel installs `requirements.txt`, serves `public/` as static assets, and runs `app.py` as a Python Function for API requests.
5. Verify the deployment by opening `/health` on its URL; it should return `{"status":"ok"}`. The frontend and API share the deployment’s origin.

## Local development

Set the Supabase values in `.env`, then run `run-local.bat` (or `python app.py`) from this directory and open `http://localhost:5000`. Flask serves both the frontend source in `frontend/` and the API, so one process is enough. If you choose to serve `frontend/` separately, its config calls the API at `http://localhost:5000`. On Vercel it uses the same origin.

Keep the four files `index.html`, `config.js`, `app.js`, and `styles.css` in `public/` synchronized with `frontend/` when changing the UI. Local Flask serves from `frontend/`; Vercel serves `public/` from its CDN.
