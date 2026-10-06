// Vercel serverless function — receives the "become a partner mover" application
// from /partners/ and emails it to the business inbox via Resend.
// Env var (set in Vercel): RESEND_API_KEY
// Unlike api/quote.js this does NOT route to partner movers or log to the sheet —
// it's an internal application, so it only emails TO.

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
  const app = {
    name: (b.name || '').toString().trim(),
    email: (b.email || '').toString().trim(),
    phone: (b.phone || '').toString().trim(),
    areas: (b.areas || '').toString().trim(),
    crew: (b.crew || '').toString().trim(),
  };

  if (!app.name || !app.email) {
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
      <h2 style="margin:0 0 12px">New Mover Application${app.name ? ' — ' + esc(app.name) : ''}</h2>
      <table style="border-collapse:collapse;font-size:14px">
        ${row('Name', app.name)}
        ${row('Email', app.email)}
        ${row('Phone', app.phone)}
        ${row('Area(s) served', app.areas)}
        ${row('About their crew', app.crew)}
      </table>
    </div>`;

  let emailResult;
  try {
    emailResult = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: FROM,
        to: [TO],
        reply_to: app.email,
        subject: `New Mover Application${app.name ? ' — ' + app.name : ''}`,
        html,
      }),
    });
  } catch (err) {
    console.error('Resend failed:', String(err));
    return res.status(502).json({ error: 'Could not send your application. Please email us instead.' });
  }

  if (!emailResult.ok) {
    const detail = await emailResult.text().catch(() => '');
    console.error('Resend failed:', detail);
    return res.status(502).json({ error: 'Could not send your application. Please email us instead.' });
  }

  // JS clients (fetch) get JSON; a plain form POST gets a redirect to the thank-you page.
  if ((req.headers['content-type'] || '').includes('application/json')) {
    return res.status(200).json({ ok: true });
  }
  res.statusCode = 303;
  res.setHeader('Location', '/thank-you/');
  res.end();
}
