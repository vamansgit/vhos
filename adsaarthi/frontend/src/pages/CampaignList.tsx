import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import type { CampaignBrief } from "@/api/types";
import { formatCurrency, titleCase } from "@/lib/format";

const STATUS_STYLES: Record<CampaignBrief["status"], string> = {
  draft: "bg-ink-100 text-ink-700",
  matching: "bg-amber-100 text-amber-800",
  matched: "bg-brand-100 text-brand-800",
  launched: "bg-blue-100 text-blue-800",
  completed: "bg-ink-200 text-ink-700",
};

export default function CampaignList() {
  const [briefs, setBriefs] = useState<CampaignBrief[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<CampaignBrief[]>("/campaigns")
      .then(setBriefs)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">Campaigns</h1>
          <p className="text-sm text-ink-500">Define a campaign intent brief and let the Auto-Match Engine do the rest.</p>
        </div>
        <Link to="/campaigns/new" className="btn-primary">
          + New Campaign Brief
        </Link>
      </div>

      {loading ? (
        <div className="text-ink-500">Loading…</div>
      ) : briefs.length === 0 ? (
        <div className="card text-center text-sm text-ink-500">
          No campaign briefs yet. Create one to get a ranked creator shortlist in minutes.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {briefs.map((b) => (
            <Link key={b.id} to={`/campaigns/${b.id}`} className="card block hover:border-brand-300">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold text-ink-900">{titleCase(b.objective)}</div>
                  <div className="text-xs text-ink-500">{titleCase(b.content_format)}</div>
                </div>
                <span className={`badge ${STATUS_STYLES[b.status]}`}>{titleCase(b.status)}</span>
              </div>
              <div className="mt-3 text-sm text-ink-600">Budget: {formatCurrency(b.total_budget)}</div>
              {b.target_audience_interests && (
                <div className="mt-1 text-xs text-ink-500">Audience: {b.target_audience_interests}</div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
