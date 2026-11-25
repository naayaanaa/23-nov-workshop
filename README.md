# Campus Connect API and frontend

This repository deploys both the Flask API and static frontend to one Vercel project. The frontend files in `public/` are served by Vercel's CDN; Flask handles the `/api/...` routes on the same domain.

## Deploy to Vercel

1. Import this Git repository and use its root directory (the folder containing `app.py`).
2. Set the framework preset to **Flask** if Vercel does not detect it automatically. Leave the build and output directory fields empty.
3. Add `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` as Vercel environment variables for Preview and Production.
4. Deploy. Vercel detects `app.py`, installs `requirements.txt`, and serves the contents of `public/`.

## Local development

Set the Supabase values in `.env` and run `python app.py` from this directory. Serve the sibling `../frontend/` folder with a static server. Its config automatically calls the backend at `http://localhost:5000`; on Vercel, it uses the same origin.

Keep the four files `index.html`, `config.js`, `app.js`, and `styles.css` in `public/` synchronized with the corresponding files in `../frontend/` when changing the UI.
