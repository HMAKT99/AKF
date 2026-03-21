import type { VercelRequest, VercelResponse } from '@vercel/node';

const MOLTBOOK_API = 'https://www.moltbook.com/api/v1';
const AGENT_NAME = 'akf-agent';
const API_KEY = process.env.MOLTBOOK_API_KEY || '';

export default async function handler(_req: VercelRequest, res: VercelResponse) {
  // Cache for 60s on CDN, serve stale for 120s while revalidating
  res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=120');
  res.setHeader('Access-Control-Allow-Origin', '*');

  try {
    // Public search endpoint works without auth — fallback if no key
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (API_KEY) headers.Authorization = `Bearer ${API_KEY}`;

    let karma = 0;
    let followers = 0;
    let posts = 0;
    let comments = 0;

    // Get agent profile stats from search
    const searchRes = await fetch(
      `${MOLTBOOK_API}/search?q=${AGENT_NAME}&type=agents&limit=1`,
      { headers }
    );
    if (searchRes.ok) {
      const searchData = await searchRes.json();
      const agent = searchData?.results?.[0];
      if (agent?.title === AGENT_NAME || agent?.name === AGENT_NAME) {
        karma = agent.upvotes ?? agent.karma ?? 0;
        followers = agent.followerCount ?? agent.followers ?? 0;
      }
    }

    // If we have auth, get richer data from /home
    if (API_KEY) {
      try {
        const homeRes = await fetch(`${MOLTBOOK_API}/home`, { headers });
        if (homeRes.ok) {
          const home = await homeRes.json();
          karma = home?.your_account?.karma ?? karma;
          const activity = home?.activity_on_your_posts ?? [];
          comments = activity.reduce(
            (sum: number, p: any) => sum + (p.new_notification_count ?? 0),
            0
          );
          posts = activity.length || posts;
        }
      } catch {}

      // Get post count from agent's posts
      try {
        const postsRes = await fetch(
          `${MOLTBOOK_API}/search?q=${AGENT_NAME}&type=posts&limit=50`,
          { headers }
        );
        if (postsRes.ok) {
          const postsData = await postsRes.json();
          const agentPosts = (postsData?.results ?? []).filter(
            (p: any) => p.author?.name === AGENT_NAME
          );
          if (agentPosts.length > 0) posts = agentPosts.length;
          // Sum up total engagement across posts
          const totalComments = agentPosts.reduce(
            (sum: number, p: any) => sum + (p.comment_count ?? p.comments ?? 0),
            0
          );
          if (totalComments > 0) comments = totalComments;
        }
      } catch {}
    }

    return res.status(200).json({ karma, followers, posts, comments });
  } catch {
    return res.status(200).json({ karma: 0, followers: 0, posts: 0, comments: 0 });
  }
}
