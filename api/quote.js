// Vercel serverless function — receives the quote form and emails it via Resend.
// Set RESEND_API_KEY in the Vercel project's Environment Variables.
// The "from" domain (smallmoverscanada.ca) must be verified in Resend.

const TO = 'info@smallmoverscanada.ca';
const FROM = 'Small Movers Canada <quote@smallmoverscanada.ca>';

const esc = (s) =>
  String(s == null ? '' : s).replace(/[<>&]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]));

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const b = req.body || {};
  const name = (b.name || '').toString().trim();
  const email = (b.email || '').toString().trim();
  const phone = (b.phone || '').toString().trim();
  const date = (b.date || '').toString().trim();
  const city = (b.city || '').toString().trim();
  const details = (b.details || '').toString().trim();

  if (!name || !email) {
    return res.status(400).json({ error: 'Name and email are required.' });
  }

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    console.error('RESEND_API_KEY is not set');
    return res.status(500).json({ error: 'Email service not configured.' });
  }

  const row = (label, val) =>
    `<tr><td style="padding:6px 12px;color:#555"><strong>${label}</strong></td>` +
    `<td style="padding:6px 12px">${esc(val) || '—'}</td></tr>`;

  const html = `
    <div style="font-family:Arial,sans-serif;color:#0E2A47">
      <h2 style="margin:0 0 12px">New Quote Request${city ? ' — ' + esc(city) : ''}</h2>
      <table style="border-collapse:collapse;font-size:14px">
        ${row('Name', name)}
        ${row('Email', email)}
        ${row('Phone', phone)}
        ${row('Date of move', date)}
        ${row('City', city)}
        ${row("What they're moving", details)}
      </table>
    </div>`;

  try {
    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: FROM,
        to: [TO],
        reply_to: email,
        subject: `New Quote Request${city ? ' — ' + city : ''}`,
        html,
      }),
    });

    if (!r.ok) {
      console.error('Resend error:', r.status, await r.text());
      return res.status(502).json({ error: 'Could not send your request. Please call us instead.' });
    }
  } catch (err) {
    console.error('Resend exception:', err);
    return res.status(502).json({ error: 'Could not send your request. Please call us instead.' });
  }

  // JS clients (fetch) get JSON; a plain form POST gets a redirect to the thank-you page.
  const ct = (req.headers['content-type'] || '');
  if (ct.includes('application/json')) {
    return res.status(200).json({ ok: true });
  }
  res.statusCode = 303;
  res.setHeader('Location', '/thank-you/');
  res.end();
}
