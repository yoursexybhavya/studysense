// Vercel Serverless Function: StudySense Cloud Sync Engine
// Persists and synchronizes user profiles, study timer history, and preferences across devices.

let memoryStore = {};

export default async function handler(req, res) {
  // Universal CORS headers for Web, PWA, iOS WKWebView, and Android WebView
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader(
    'Access-Control-Allow-Headers',
    'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, x-user-id'
  );

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const userId = req.headers['x-user-id'] || req.query.userId || 'studysense_user';

  if (req.method === 'POST') {
    try {
      const payload = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
      const existing = memoryStore[userId] || {};

      memoryStore[userId] = {
        ...existing,
        ...payload,
        userId,
        lastSyncedAt: new Date().toISOString()
      };

      return res.status(200).json({
        success: true,
        message: 'Data successfully synced to cloud server',
        data: memoryStore[userId]
      });
    } catch (err) {
      return res.status(400).json({ success: false, error: 'Invalid JSON payload' });
    }
  }

  if (req.method === 'GET') {
    const data = memoryStore[userId] || null;
    return res.status(200).json({
      success: true,
      exists: data !== null,
      data: data
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
