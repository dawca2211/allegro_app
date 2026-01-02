<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1tTlWBef7Yv2-6sNGA86QHm3HlpVGeqg5

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## Environment variables for Allegro & Supabase

The app requires several environment variables for the Allegro OAuth flow and Supabase access. Create a `.env.local` (or set these in your deployment) with:

- `ALLEGRO_CLIENT_ID` — Allegro OAuth client ID.
- `ALLEGRO_CLIENT_SECRET` — Allegro OAuth client secret.
- `ALLEGRO_REDIRECT_URI` — Redirect URI registered in Allegro (default: `https://allegro-app.vercel.app/api/auth/callback`).
- `ALLEGRO_DEFAULT_USER_EMAIL` — Optional default user email used in the `allegro_tokens` upsert (default: `admin`).
- `SUPABASE_URL` — Your Supabase project URL.
- `SUPABASE_SERVICE_ROLE_KEY` — Supabase service role key (server-side only; keep secret).

Notes:
- Do not expose `SUPABASE_SERVICE_ROLE_KEY` in client-side code or public repos.
- Ensure `ALLEGRO_REDIRECT_URI` matches the value registered in your Allegro OAuth application.
