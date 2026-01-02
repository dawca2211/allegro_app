export default function handler(req: any, res: any) {
  try {
    const CLIENT_ID = process.env.ALLEGRO_CLIENT_ID;
    const REDIRECT_URI = process.env.ALLEGRO_REDIRECT_URI || 'https://allegro-app.vercel.app/api/auth/callback';

    if (!CLIENT_ID) {
      return res.status(500).json({ error: 'Brak ustawionego ALLEGRO_CLIENT_ID w env' });
    }

    const authUrl = `https://allegro.pl/auth/oauth/authorize?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}`;
    return res.redirect(authUrl);
  } catch (err) {
    console.error('auth handler error', err);
    return res.status(500).json({ error: 'Błąd podczas przygotowywania autoryzacji' });
  }
}