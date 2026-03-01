import type { Claim } from "./akf";

// ── Scenario 1: Developer Workflow ──────────────────────────────────────────

export const DEV_SCENARIO = {
  question: "What's the best caching strategy for our user API?",

  copilotResponse: `Based on your codebase, I recommend a **Redis-backed cache** with TTL-based invalidation:

\`\`\`typescript
import Redis from 'ioredis';
const redis = new Redis(process.env.REDIS_URL);

export async function getCachedUser(id: string) {
  const cached = await redis.get(\`user:\${id}\`);
  if (cached) return JSON.parse(cached);

  const user = await db.users.findById(id);
  await redis.set(\`user:\${id}\`, JSON.stringify(user), 'EX', 300);
  return user;
}
\`\`\`

This gives you sub-millisecond reads with automatic 5-minute expiry. Redis handles cache invalidation gracefully under connection failures — the app falls through to the database.`,

  claims: [
    { c: "Redis-backed cache with TTL is the recommended pattern for user API endpoints", t: 0.88, tier: 2, ai: true, src: "Architecture best practices", id: "dev-c1" },
    { c: "5-minute TTL (300s) balances freshness with read performance for user data", t: 0.75, tier: 4, ai: true, src: "Copilot inference from codebase patterns", id: "dev-c2", risk: "TTL value is a general recommendation — not tuned to this specific workload" },
    { c: "ioredis library is production-ready with connection pooling support", t: 0.95, tier: 1, ai: true, src: "npm registry / GitHub stats", id: "dev-c3" },
  ] as Claim[],

  codeFile: `import express from 'express';
import { db } from '../db';

const router = express.Router();

// TODO: Add caching — currently hitting DB on every request
router.get('/users/:id', async (req, res) => {
  const user = await db.users.findById(req.params.id);
  if (!user) return res.status(404).json({ error: 'Not found' });
  res.json(user);
});

export default router;`,

  prTitle: "feat: Add Redis caching for user API",
  prNumber: 247,
  author: "dev@contoso.com",
  reviewer: "lead@contoso.com",
};

// ── Scenario 2: Analyst Workflow ────────────────────────────────────────────

export const ANALYST_SCENARIO = {
  spreadsheet: [
    { metric: "Revenue ($B)", q1: "3.8", q2: "4.0", q3: "4.2", q4: "—" },
    { metric: "Cloud Growth", q1: "12%", q2: "14%", q3: "17%", q4: "—" },
    { metric: "Enterprise Deals (>$10M)", q1: "8", q2: "12", q3: "15", q4: "—" },
    { metric: "AI Copilot Adoption", q1: "22%", q2: "28%", q3: "34%", q4: "—" },
    { metric: "Operating Margin", q1: "26%", q2: "27%", q3: "28%", q4: "—" },
  ],

  copilotSummary:
    "**Q3 Performance Summary**\n\nRevenue reached $4.2B (+12% YoY), driven by enterprise cloud adoption and AI workload growth. Cloud segment accelerated to 17% growth (from 14% Q2). Enterprise pipeline expanded to 15 active deals over $10M.\n\n**Key Risk:** AI copilot adoption metric (34%) is based on McKinsey survey data with uncertain methodology. Q4 projections depend on closing 3 large pipeline deals.",

  claims: [
    { c: "Woodgrove Q3 revenue was $4.2B, up 12% YoY", t: 0.98, tier: 1, src: "SEC 10-Q Filing", id: "an-c1", ver: true, ver_by: "sarah@woodgrove.com" },
    { c: "Cloud segment grew 17% driven by AI workloads", t: 0.85, tier: 2, src: "Gartner Cloud Report 2025", id: "an-c2", ai: true },
    { c: "Enterprise pipeline strong with 15 deals over $10M", t: 0.72, tier: 4, src: "Internal CRM data", id: "an-c3" },
    { c: "AI copilot adoption rate is 34% across Fortune 500", t: 0.78, tier: 2, ai: true, src: "McKinsey AI Survey 2025", id: "an-c4", risk: "Survey methodology uncertain" },
  ] as Claim[],

  author: "sarah@woodgrove.com",
  docTitle: "Woodgrove-Q3-Analysis.xlsx",
};

// ── Scenario 3: Pipeline Workflow ───────────────────────────────────────────

export const PIPELINE_SCENARIO = {
  sources: [
    {
      name: "Market Data",
      filename: "market-data.akf",
      icon: "chart",
      claims: [
        { c: "Cloud infrastructure market grew 22% in H1 2025", t: 0.95, tier: 1, src: "IDC Market Report", id: "mkt-c1" },
        { c: "Woodgrove holds 18% cloud market share in enterprise segment", t: 0.88, tier: 2, src: "Gartner Magic Quadrant", id: "mkt-c2" },
      ] as Claim[],
    },
    {
      name: "CRM Analysis",
      filename: "crm-analysis.akf",
      icon: "users",
      claims: [
        { c: "Pipeline includes 8 deals over $20M expected to close in Q4", t: 0.72, tier: 4, src: "Salesforce CRM export", id: "crm-c1" },
        { c: "Customer renewal rate is 94% for AI platform subscribers", t: 0.82, tier: 3, src: "Customer success data", id: "crm-c2" },
      ] as Claim[],
    },
    {
      name: "News Sentiment",
      filename: "news-sentiment.akf",
      icon: "news",
      claims: [
        { c: "Industry analysts expect 30% growth in AI infrastructure spending", t: 0.68, tier: 3, ai: true, src: "News aggregation + NLP", id: "news-c1" },
        { c: "Competitor Contoso pivoting away from cloud, creating market opportunity", t: 0.55, tier: 5, ai: true, src: "AI sentiment analysis", id: "news-c2", risk: "Inferred from limited news articles; competitor strategy not confirmed" },
      ] as Claim[],
    },
  ],
  decisionQuestion: "Should Woodgrove invest $200M in AI cloud platform expansion?",
};
