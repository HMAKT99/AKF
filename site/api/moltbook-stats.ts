import type { VercelRequest, VercelResponse } from '@vercel/node';

const MOLTBOOK_API = 'https://www.moltbook.com/api/v1';
const AGENT_NAME = 'akf-agent';

export default async function handler(_req: VercelRequest, res: VercelResponse) {
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=120');
  res.setHeader('Access-Control-Allow-Origin', '*');

  try {
    // All three calls are public — no API key needed
    const [agentRes, postsRes, mentionsRes] = await Promise.all([
      fetch(`${MOLTBOOK_API}/search?q=${AGENT_NAME}&type=agents&limit=1`),
      fetch(`${MOLTBOOK_API}/search?q=akf&type=posts&limit=50`),
      fetch(`${MOLTBOOK_API}/search?q=${AGENT_NAME}&type=comments&limit=50`),
    ]);

    let karma = 0;
    if (agentRes.ok) {
      const data = await agentRes.json();
      const agent = data?.results?.[0];
      if (agent?.title === AGENT_NAME) {
        karma = agent.upvotes ?? 0;
      }
    }

    let posts = 0;
    if (postsRes.ok) {
      const data = await postsRes.json();
      posts = (data?.results ?? []).filter(
        (p: any) => p.author?.name === AGENT_NAME
      ).length;
    }

    let mentions = 0;
    if (mentionsRes.ok) {
      const data = await mentionsRes.json();
      mentions = data?.count ?? data?.results?.length ?? 0;
    }

    return res.status(200).json({ karma, posts, mentions });
  } catch {
    return res.status(200).json({ karma: 0, posts: 0, mentions: 0 });
  }
}
