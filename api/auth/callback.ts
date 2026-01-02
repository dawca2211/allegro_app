import { createClient } from '@supabase/supabase-js';
import type { NextApiRequest, NextApiResponse } from 'next';

// Inicjalizacja połączenia z bazą
const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { code } = req.query;
  if (!code) return res.status(400).json({ error: 'Brak kodu' });

  const basicAuth = Buffer.from(`${process.env.ALLEGRO_CLIENT_ID}:${process.env.ALLEGRO_CLIENT_SECRET}`).toString('base64');
  const redirectUri = process.env.ALLEGRO_REDIRECT_URI || 'https://allegro-app.vercel.app/api/auth/callback';

  try {
    // 1. Pobieramy tokeny z Allegro
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

    const data = await response.json();
    if (!response.ok) {
      console.error('Allegro token endpoint error:', data);
      throw data;
    }

    // 2. ZAPIS DO SUPABASE (To sprawi, że tabela nie będzie pusta)
    const defaultUserEmail = process.env.ALLEGRO_DEFAULT_USER_EMAIL || 'admin';
    const { error } = await supabase
      .from('allegro_tokens')
      .upsert({
        user_email: defaultUserEmail,
        access_token: data.access_token,
        refresh_token: data.refresh_token
      }, { onConflict: 'user_email' });

    if (error) {
      console.error('Błąd zapisu w bazie:', error);
      return res.status(500).json({ error: 'Baza danych odrzuciła zapis', details: error });
    }

    // 3. Po udanym zapisie PRZEKIERUJ do aplikacji, zamiast pokazywać JSON
    res.redirect('/?auth=success');
    return;

  } catch (err: any) {
    res.status(500).json({ error: 'Błąd krytyczny', details: err });
  }
}