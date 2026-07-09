import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { AdPlatform, Influencer, InfluencerCategory } from "@/api/types";
import { formatCurrency, formatNumber, formatPct, titleCase } from "@/lib/format";

const CATEGORIES: InfluencerCategory[] = [
  "beauty",
  "fashion",
  "wellness",
  "food",
  "tech",
  "home",
  "fitness",
  "parenting",
  "finance",
  "travel",
];

export default function InfluencerDirectory() {
  const [influencers, setInfluencers] = useState<Influencer[]>([]);
  const [category, setCategory] = useState<InfluencerCategory | "">("");
  const [platform, setPlatform] = useState<AdPlatform | "">("");
  const [minEngagement, setMinEngagement] = useState("");
  const [loading, setLoading] = useState(true);
  const [compareIds, setCompareIds] = useState<string[]>([]);

  async function load() {
    setLoading(true);
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (platform) params.set("platform", platform);
    if (minEngagement) params.set("min_engagement_pct", minEngagement);
    const data = await api.get<Influencer[]>(`/influencers?${params.toString()}`);
    setInfluencers(data);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [category, platform, minEngagement]);

  function toggleCompare(id: string) {
    setCompareIds((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : prev.length < 4 ? [...prev, id] : prev
    );
  }

  const compareList = influencers.filter((i) => compareIds.includes(i.id));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">Influencer Directory</h1>
        <p className="text-sm text-ink-500">
          Manual search always available alongside the auto-match campaign flow. Select up to 4 to compare.
        </p>
      </div>

      <div className="card flex flex-wrap gap-4">
        <div className="w-40">
          <label className="label">Category</label>
          <select className="input" value={category} onChange={(e) => setCategory(e.target.value as InfluencerCategory | "")}>
            <option value="">All</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {titleCase(c)}
              </option>
            ))}
          </select>
        </div>
        <div className="w-40">
          <label className="label">Platform</label>
          <select className="input" value={platform} onChange={(e) => setPlatform(e.target.value as AdPlatform | "")}>
            <option value="">All</option>
            <option value="meta">Meta (Instagram)</option>
            <option value="youtube">YouTube</option>
          </select>
        </div>
        <div className="w-48">
          <label className="label">Min. engagement rate %</label>
          <input
            className="input"
            type="number"
            step="0.1"
            value={minEngagement}
            onChange={(e) => setMinEngagement(e.target.value)}
            placeholder="e.g. 3"
          />
        </div>
      </div>

      {compareList.length > 0 && (
        <div className="card overflow-x-auto">
          <h2 className="mb-3 text-sm font-semibold text-ink-900">Comparing {compareList.length} creators</h2>
          <table className="w-full min-w-[600px] text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-ink-500">
                <th className="pb-2">Creator</th>
                {compareList.map((i) => (
                  <th key={i.id} className="pb-2">
                    @{i.handle}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                ["Category", (i: Influencer) => titleCase(i.category)],
                ["Followers", (i: Influencer) => formatNumber(i.follower_count)],
                ["Engagement", (i: Influencer) => formatPct(i.engagement_rate_pct)],
                ["Consistency", (i: Influencer) => `${i.posting_consistency_score}/100`],
                ["Price range", (i: Influencer) => `${formatCurrency(i.indicative_price_min)}–${formatCurrency(i.indicative_price_max)}`],
                ["Past campaigns", (i: Influencer) => formatNumber(i.historical_campaigns_count)],
              ].map(([label, getter]) => (
                <tr key={label as string} className="border-t border-ink-100">
                  <td className="py-2 text-ink-500">{label as string}</td>
                  {compareList.map((i) => (
                    <td key={i.id} className="py-2 font-medium">
                      {(getter as (i: Influencer) => string)(i)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {loading ? (
        <div className="text-ink-500">Loading directory…</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {influencers.map((inf) => (
            <div key={inf.id} className="card">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold text-ink-900">@{inf.handle}</div>
                  <div className="text-xs text-ink-500">
                    {titleCase(inf.platform)} · {titleCase(inf.category)}
                  </div>
                </div>
                <label className="flex items-center gap-1.5 text-xs text-ink-500">
                  <input
                    type="checkbox"
                    checked={compareIds.includes(inf.id)}
                    onChange={() => toggleCompare(inf.id)}
                  />
                  Compare
                </label>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <div>
                  <div className="text-xs text-ink-500">Followers</div>
                  <div className="font-medium">{formatNumber(inf.follower_count)}</div>
                </div>
                <div>
                  <div className="text-xs text-ink-500">Engagement</div>
                  <div className="font-medium">{formatPct(inf.engagement_rate_pct)}</div>
                </div>
                <div>
                  <div className="text-xs text-ink-500">Price range</div>
                  <div className="font-medium">
                    {formatCurrency(inf.indicative_price_min)}–{formatCurrency(inf.indicative_price_max)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-ink-500">Past campaigns</div>
                  <div className="font-medium">{inf.historical_campaigns_count}</div>
                </div>
              </div>
              {inf.top_content_style && <p className="mt-3 text-xs text-ink-500">{inf.top_content_style}</p>}
            </div>
          ))}
          {influencers.length === 0 && <p className="text-sm text-ink-500">No creators match these filters.</p>}
        </div>
      )}
    </div>
  );
}
