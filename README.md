# encuentra

## Environment switching (Supabase)

This repo uses environment variables to switch cleanly between development and production for both the frontend and backend.

- Frontend (Vite):
	- Uses `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` from env files.
	- Already configured to read from `.env.local` in development.
	- For production builds, use `frontend/.env.production` with your production project URL and anon key. Vite automatically picks it when building with `--mode production` or `npm run build`.

- Backend (FastAPI):
	- Reads env from `.env.<APP_ENV>` first, then falls back to `.env` at the repo root.
	- Set `APP_ENV=production` to load `.env.production` before `.env`.