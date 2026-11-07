// Vercel serverless function — receives the demolition-vertical quote form and
// emails it via Resend. De-branded lead-gen: the customer sees the partner's
// brand (Hauling Heroes); this routes the lead to the partner's inbox + info@.
// Calls are tracked separately via the DMO Twilio line; this handles web forms.
//
// Env vars (set in Vercel): RESEND_API_KEY — Resend key (same verified
// smallmoverscanada.ca sending domain as /api/quote).
//
// Routing is keyed by the form's hidden `service` + `city` so one endpoint can
// serve more demolition cities later without trusting a client-supplied address.
const INFO = 'info@smallmoverscanada.ca';
const FROM = 'Hauling Heroes <quote@smallmoverscanada.ca>';

// service|city (lowercased) -> partner inbox that works these leads.
const ROUTES = {
  'demolition|edmonton': 'HaulingheroesLimited@gmail.com',
};

const esc = (s) =>
  String(s == null ? '' : s).replace(/[<>&]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' }[c]));

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const b = req.body || {};
  const wantsJson = (req.headers['content-type'] || '').includes('application/json');

  // Honeypot: real users never fill `company`. Pretend success, send nothing.
  if ((b.company || '').toString().trim()) {
    if (wantsJson) return res.status(200).json({ ok: true });
    return thanks(res);
  }

  const lead = {
    name: (b.name || '').toString().trim(),
    phone: (b.phone || '').toString().trim(),
    email: (b.email || '').toString().trim(),
    job: (b.job || '').toString().trim(),
    area: (b.area || '').toString().trim(),
    details: (b.details || '').toString().trim(),
    service: (b.service || 'Demolition').toString().trim(),
    city: (b.city || '').toString().trim(),
  };

  if (!lead.name || !lead.phone) {
    return res.status(400).json({ error: 'Name and phone are required.' });
  }

  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    console.error('RESEND_API_KEY is not set');
    return res.status(500).json({ error: 'Email service not configured.' });
  }

  const key = `${lead.service}|${lead.city}`.toLowerCase();
  const partner = ROUTES[key];
  const recipients = partner ? [INFO, partner] : [INFO];

  const row = (label, val) =>
    `<tr><td style="padding:6px 12px;color:#555"><strong>${label}</strong></td>` +
    `<td style="padding:6px 12px">${esc(val) || '—'}</td></tr>`;

  const html = `
    <div style="font-family:Arial,sans-serif;color:#16202d">
      <h2 style="margin:0 0 12px">New ${esc(lead.service)} Lead${lead.city ? ' — ' + esc(lead.city) : ''}</h2>
      <table style="border-collapse:collapse;font-size:14px">
        ${row('Name', lead.name)}
        ${row('Phone', lead.phone)}
        ${row('Email', lead.email)}
        ${row('Job type', lead.job)}
        ${row('Area', lead.area)}
        ${row('Details', lead.details)}
        ${row('City', lead.city)}
      </table>
    </div>`;

  let ok = false;
  try {
    const r = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from: FROM,
        to: recipients,
        reply_to: lead.email || undefined,
        subject: `New ${lead.service} Lead${lead.city ? ' — ' + lead.city : ''}`,
        html,
      }),
    });
    ok = r.ok;
    if (!ok) console.error('Resend failed:', await r.text().catch(() => ''));
  } catch (err) {
    console.error('Resend threw:', String(err));
  }

  if (!ok) {
    if (wantsJson) return res.status(502).json({ error: 'Could not send. Please call us instead.' });
    return res.status(502).send('Sorry — we could not send your request. Please call us instead.');
  }

  if (wantsJson) return res.status(200).json({ ok: true });
  return thanks(res);
}

function thanks(res) {
  res.setHeader('Content-Type', 'text/html; charset=utf-8');
  return res.status(200).send(
    '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<title>Thanks</title><body style="font-family:Arial,sans-serif;background:#0c2d54;color:#fff;' +
    'display:flex;min-height:100vh;align-items:center;justify-content:center;text-align:center;margin:0">' +
    '<div style="max-width:460px;padding:24px"><h1 style="color:#ef5a22">Thanks</h1>' +
    "<p>We've got your request and will call you back shortly to set up your free on-site quote.</p>" +
    '<p><a href="/" style="color:#9ec3ea">Back</a></p></div></body>');
}
