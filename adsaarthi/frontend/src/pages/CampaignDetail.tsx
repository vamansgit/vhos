import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, ApiError } from "@/api/client";
import type { CampaignBrief, MatchResult, MatchStatus } from "@/api/types";
import { formatCurrency, formatNumber, titleCase } from "@/lib/format";

const CHECKLIST_ITEMS = [
  "Creative sizes confirmed for each placement",
  "UTM tagging set on all campaign links",
  "Budget caps configured per platform",
  "Target audience notes shared with creative team",
  "Approved creator bids and content drafts reviewed",
];

const STATUS_STYLES: Record<MatchStatus, string> = {
  pending_review: "bg-amber-100 text-amber-800",
  approved: "bg-brand-100 text-brand-800",
  adjusted: "bg-blue-100 text-blue-800",
  rejected: "bg-red-100 text-red-700",
};

export default function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const [brief, setBrief] = useState<CampaignBrief | null>(null);
  const [matches, setMatches] = useState<MatchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [matching, setMatching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checklist, setChecklist] = useState<boolean[]>(CHECKLIST_ITEMS.map(() => false));
  const [bidDrafts, setBidDrafts] = useState<Record<string, string>>({});

  async function load() {
    if (!id) return;
    setLoading(true);
    const [b, m] = await Promise.all([
      api.get<CampaignBrief>(`/campaigns/${id}`),
      api.get<MatchResult[]>(`/campaigns/${id}/matches`),
    ]);
    setBrief(b);
    setMatches(m);
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function runMatch() {
    if (!id) return;
    setMatching(true);
    setError(null);
    try {
      const results = await api.post<MatchResult[]>(`/campaigns/${id}/match`);
      setMatches(results);
      const b = await api.get<CampaignBrief>(`/campaigns/${id}`);
      setBrief(b);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Matching failed");
    } finally {
      setMatching(false);
    }
  }

  async function reviewMatch(matchId: string, status: MatchStatus, approvedBid?: number) {
    if (!id) return;
    const updated = await api.patch<MatchResult>(`/campaigns/${id}/matches/${matchId}`, {
      status,
      approved_bid: approvedBid,
    });
    setMatches((prev) => prev.map((m) => (m.id === matchId ? updated : m)));
  }

  async function exportBrief() {
    if (!id) return;
    const text = await api.get<string>(`/campaigns/${id}/export`);
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `campaign-brief-${id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading || !brief) return <div className="text-ink-500">Loading…</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">
            {titleCase(brief.objective)} — {titleCase(brief.content_format)}
          </h1>
          <p className="text-sm text-ink-500">
            Budget {formatCurrency(brief.total_budget)} · Status {titleCase(brief.status)}
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" onClick={exportBrief}>
            Export Brief
          </button>
          <button className="btn-primary" onClick={runMatch} disabled={matching}>
            {matching ? "Matching…" : matches.length > 0 ? "Re-run Auto-Match" : "Run Auto-Match"}
          </button>
        </div>
      </div>

      {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

      <div className="card grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
        <div>
          <div className="text-xs text-ink-500">Audience</div>
          <div className="font-medium">{brief.target_audience_interests || "—"}</div>
        </div>
        <div>
          <div className="text-xs text-ink-500">Geography</div>
          <div className="font-medium">{brief.target_audience_geography || "—"}</div>
        </div>
        <div>
          <div className="text-xs text-ink-500">Desired reach</div>
          <div className="font-medium">{formatNumber(brief.desired_reach)}</div>
        </div>
        <div>
          <div className="text-xs text-ink-500">Format</div>
          <div className="font-medium">{titleCase(brief.content_format)}</div>
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-ink-900">
          Ranked Creator Shortlist{matches.length > 0 ? ` (${matches.length})` : ""}
        </h2>
        <p className="mb-3 text-xs text-ink-500">
          Every match requires your review before outreach or spend commitment — matched creators, bids, and
          content drafts never go out automatically.
        </p>
        {matches.length === 0 ? (
          <div className="card text-center text-sm text-ink-500">
            No matches yet. Run Auto-Match to get a ranked shortlist with bid recommendations.
          </div>
        ) : (
          <div className="space-y-3">
            {matches.map((m) => (
              <div key={m.id} className="card">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-ink-900">@{m.influencer.handle}</span>
                      <span className="badge bg-ink-100 text-ink-600">{m.tier}</span>
                      <span className={`badge ${STATUS_STYLES[m.status]}`}>{titleCase(m.status)}</span>
                    </div>
                    <div className="text-xs text-ink-500">
                      {titleCase(m.influencer.platform)} · {titleCase(m.influencer.category)} ·{" "}
                      {formatNumber(m.influencer.follower_count)} followers
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-brand-700">{m.fit_score}/100</div>
                    <div className="text-xs text-ink-500">Fit Score</div>
                  </div>
                </div>

                <p className="mt-2 text-sm text-ink-600">{m.reason}</p>

                <div className="mt-3 grid grid-cols-3 gap-3 text-xs text-ink-500">
                  <div>Engagement {m.engagement_quality_score}/100</div>
                  <div>Audience fit {m.audience_overlap_score}/100</div>
                  <div>Consistency {m.consistency_score}/100</div>
                </div>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-ink-100 pt-3">
                  <div className="text-sm">
                    <span className="text-ink-500">Recommended bid: </span>
                    <span className="font-semibold">{formatCurrency(m.recommended_bid)}</span>
                    <span className="ml-3 text-ink-500">Projected reach: </span>
                    <span className="font-semibold">{formatNumber(m.projected_reach)}</span>
                  </div>
                  {m.status === "pending_review" && (
                    <div className="flex items-center gap-2">
                      <input
                        className="input w-28"
                        type="number"
                        placeholder="Adjust bid"
                        value={bidDrafts[m.id] ?? ""}
                        onChange={(e) => setBidDrafts((prev) => ({ ...prev, [m.id]: e.target.value }))}
                      />
                      <button
                        className="btn-secondary"
                        onClick={() =>
                          reviewMatch(
                            m.id,
                            "adjusted",
                            bidDrafts[m.id] ? Number(bidDrafts[m.id]) : m.recommended_bid
                          )
                        }
                      >
                        Adjust
                      </button>
                      <button className="btn-danger" onClick={() => reviewMatch(m.id, "rejected")}>
                        Reject
                      </button>
                      <button className="btn-primary" onClick={() => reviewMatch(m.id, "approved")}>
                        Approve
                      </button>
                    </div>
                  )}
                  {m.status === "approved" && (
                    <div className="text-sm font-medium text-brand-700">
                      Approved at {formatCurrency(m.approved_bid ?? m.recommended_bid)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Pre-launch Checklist</h2>
        <div className="space-y-2">
          {CHECKLIST_ITEMS.map((item, idx) => (
            <label key={item} className="flex items-center gap-2 text-sm text-ink-700">
              <input
                type="checkbox"
                checked={checklist[idx]}
                onChange={() =>
                  setChecklist((prev) => prev.map((v, i) => (i === idx ? !v : v)))
                }
              />
              {item}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
