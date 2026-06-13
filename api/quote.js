// Vercel serverless function — receives the quote form, emails it via Resend, and
// appends the lead to a Google Sheet (Apps Script web app).
// Env vars (set in Vercel):
//   RESEND_API_KEY            — Resend API key (required to email)
//   GOOGLE_SHEETS_WEBHOOK_URL — Apps Script /exec URL (optional; skipped if unset)
// The Resend "from" domain (smallmoverscanada.ca) must be verified in Resend.

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
  const lead = {
    name: (b.name || '').toString().trim(),
    email: (b.email || '').toString().trim(),
    phone: (b.phone || '').toString().trim(),
    date: (b.date || '').toString().trim(),
    city: (b.city || '').toString().trim(),
    details: (b.details || '').toString().trim(),
  };

  if (!lead.name || !lead.email) {
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
      <h2 style="margin:0 0 12px">New Quote Request${lead.city ? ' — ' + esc(lead.city) : ''}</h2>
      <table style="border-collapse:collapse;font-size:14px">
        ${row('Name', lead.name)}
        ${row('Email', lead.email)}
        ${row('Phone', lead.phone)}
        ${row('Date of move', lead.date)}
        ${row('City', lead.city)}
        ${row("What they're moving", lead.details)}
      </table>
    </div>`;

  const emailPromise = fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      from: FROM,
      to: [TO],
      reply_to: lead.email,
      subject: `New Quote Request${lead.city ? ' — ' + lead.city : ''}`,
      html,
    }),
  });

  const sheetUrl = process.env.GOOGLE_SHEETS_WEBHOOK_URL;
  const sheetPromise = sheetUrl
    ? fetch(sheetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lead),
      })
    : Promise.resolve(null);

  const [emailResult, sheetResult] = await Promise.allSettled([emailPromise, sheetPromise]);

  // Email is the critical path — fail the request only if it didn't send.
  if (emailResult.status !== 'fulfilled' || !emailResult.value.ok) {
    const detail = emailResult.status === 'fulfilled'
      ? await emailResult.value.text().catch(() => '')
      : String(emailResult.reason);
    console.error('Resend failed:', detail);
    return res.status(502).json({ error: 'Could not send your request. Please call us instead.' });
  }

  // Sheet append is best-effort — log but don't fail the lead.
  if (sheetUrl && (sheetResult.status !== 'fulfilled' || !sheetResult.value.ok)) {
    const detail = sheetResult.status === 'fulfilled'
      ? sheetResult.value.status
      : String(sheetResult.reason);
    console.error('Sheet append failed:', detail);
  }

  // JS clients (fetch) get JSON; a plain form POST gets a redirect to the thank-you page.
  if ((req.headers['content-type'] || '').includes('application/json')) {
    return res.status(200).json({ ok: true });
  }
  res.statusCode = 303;
  res.setHeader('Location', '/thank-you/');
  res.end();
}
