import { VercelRequest, VercelResponse } from '@vercel/node';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_ROLE_KEY!);

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    // 1. Pobierz token z bazy danych
    const { data: tokenData, error: dbError } = await supabase
      .from('allegro_tokens')
      .select('access_token')
      .single();

    if (dbError || !tokenData) throw new Error('Brak tokena w bazie. Zaloguj się ponownie.');

    // 2. Zapytaj Allegro o zamówienia (ostatnie 20)
    const allegroRes = await fetch('https://api.allegro.pl/order/checkout-forms?limit=20', {
      headers: {
        'Authorization': `Bearer ${tokenData.access_token}`,
        'Accept': 'application/vnd.allegro.public.v1+json'
      }
    });

    const orders = await allegroRes.json();
    
    // 3. Zwróć dane do front-endu
    res.status(200).json(orders.checkoutForms || []);

  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
}
