import { VercelRequest, VercelResponse } from '@vercel/node';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export default async function handler(req: VercelRequest, res: VercelResponse) {
  try {
    // 1. Pobierz token z bazy danych
    const { data: tokenData, error: dbError } = await supabase
      .from('allegro_tokens')
      .select('access_token')
      .eq('user_email', 'admin')
      .single();

    if (dbError || !tokenData) {
      return res.status(401).json({ error: 'Nie znaleziono tokenu Allegro w bazie danych.' });
    }

    // 2. Zapytaj Allegro o listę zamówień
    const allegroRes = await fetch('https://api.allegro.pl/order/checkout-forms', {
      headers: {
        'Authorization': `Bearer ${tokenData.access_token}`,
        'Accept': 'application/vnd.allegro.public.v1+json'
      }
    });

    const data = await allegroRes.json();

    if (!allegroRes.ok) {
      return res.status(allegroRes.status).json({ error: 'Błąd Allegro', details: data });
    }

    // 3. Spróbuj zapisać/aktualizować zamówienia w tabeli `orders` (UPSERT)
    try {
      const checkoutForms = Array.isArray(data?.checkoutForms) ? data.checkoutForms : [];
      if (checkoutForms.length > 0) {
        const records = checkoutForms.map((order: any) => ({
          allegro_id: order?.id ?? null,
          buyer_login: order?.buyer?.login ?? null,
          total_amount: parseFloat(order?.summary?.totalToPay?.amount ?? '0') || 0,
          status: order?.fulfillment?.status ?? null,
          updated_at: order?.updatedAt ?? null,
          data: order ?? null
        }));

        // Fire-and-forget: nie blokujemy odpowiedzi na front-end w przypadku problemów z zapisem,
        // ale logujemy błędy do konsoli. Korzystamy z SUPABASE_SERVICE_ROLE_KEY skonfigurowanego wyżej.
        supabase
          .from('orders')
          .upsert(records, { onConflict: 'allegro_id' })
          .then(({ error: upsertError }) => {
            if (upsertError) console.error('Supabase upsert error:', upsertError);
          })
          .catch((e) => console.error('Supabase upsert exception:', e));
      }
    } catch (e: any) {
      console.error('Error preparing orders for upsert:', e);
    }

    // 4. Zwróć zamówienia do front-endu (nawet jeśli zapis do Supabase nie powiódł się)
    res.status(200).json(data.checkoutForms || []);

  } catch (err: any) {
    res.status(500).json({ error: 'Błąd serwera', message: err.message });
  }
}