export default async function handler(req: any, res: any) {
  const { code } = req.query;
  if (!code) return res.status(400).send('Brak kodu autoryzacji');

  const clientId = process.env.ALLEGRO_CLIENT_ID;
  const clientSecret = process.env.ALLEGRO_CLIENT_SECRET;
  const redirectUri = process.env.ALLEGRO_REDIRECT_URI || 'https://allegro-app.vercel.app/api/auth/callback';

  if (!clientId || !clientSecret) {
    return res.status(500).json({ error: 'Brak konfiguracji klienta Allegro w zmiennych środowiskowych' });
  }

  const basicAuth = Buffer.from(`${clientId}:${clientSecret}`).toString('base64');

  try {
    const response = await fetch('https://allegro.pl/auth/oauth/token', {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${basicAuth}`,
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        code: code as string,
        redirect_uri: redirectUri
      })
    });

    if (!response.ok) {
      const text = await response.text();
      console.error('allegro token error', response.status, text);
      return res.status(502).json({ error: 'Błąd od serwera Allegro podczas wymiany tokena', details: text });
    }

    const tokens = await response.json();
    // TODO: zapisz tokeny w bezpiecznym magazynie (Supabase / DB)
    return res.status(200).json({ status: 'Połączono!', message: 'Teraz system może czytać Twoje dane.', tokens });
  } catch (error) {
    console.error('auth callback error', error);
    return res.status(500).json({ error: 'Błąd autoryzacji' });
  }
}