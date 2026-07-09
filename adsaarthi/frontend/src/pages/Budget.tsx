import { useEffect, useState } from "react";
import { api, ApiError } from "@/api/client";
import type { BudgetRecommendation } from "@/api/types";
import { formatCurrency } from "@/lib/format";

interface CollaborationLog {
  id: string;
  influencer_name: string;
  cost: number;
  conversions_attributed: number;
  notes: string | null;
}

const TREND_STYLES: Record<BudgetRecommendation["trend"], string> = {
  improving: "border-brand-200 bg-brand-50 text-brand-800",
  worsening: "border-amber-200 bg-amber-50 text-amber-800",
  stable: "border-ink-200 bg-ink-50 text-ink-700",
};

export default function Budget() {
  const [recommendation, setRecommendation] = useState<BudgetRecommendation | null>(null);
  const [logs, setLogs] = useState<CollaborationLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [form, setForm] = useState({ influencer_name: "", cost: "", conversions_attributed: "0", notes: "" });
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    const [rec, logData] = await Promise.all([
      api.get<BudgetRecommendation>("/budget/recommendation"),
      api.get<CollaborationLog[]>("/budget/collaborations"),
    ]);
    setRecommendation(rec);
    setLogs(logData);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function refresh() {
    setRefreshing(true);
    const rec = await api.get<BudgetRecommendation>("/budget/recommendation");
    setRecommendation(rec);
    setRefreshing(false);
  }

  async function logCollaboration(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/budget/collaborations", {
        influencer_name: form.influencer_name,
        cost: Number(form.cost),
        conversions_attributed: Number(form.conversions_attributed || 0),
        notes: form.notes || null,
      });
      setForm({ influencer_name: "", cost: "", conversions_attributed: "0", notes: "" });
      const logData = await api.get<CollaborationLog[]>("/budget/collaborations");
      setLogs(logData);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to log collaboration");
    }
  }

  if (loading) return <div className="text-ink-500">Loading…</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">Budget & Channel Optimizer</h1>
        <p className="text-sm text-ink-500">
          A transparent, rules-based advisory layer — not a black-box auto-optimizer.
        </p>
      </div>

      {recommendation && (
        <div className={`card border ${TREND_STYLES[recommendation.trend]}`}>
          <div className="flex items-center justify-between">
            <span className="badge bg-white/60">{recommendation.trend.toUpperCase()}</span>
            <button className="btn-secondary" onClick={refresh} disabled={refreshing}>
              {refreshing ? "Refreshing…" : "Refresh"}
            </button>
          </div>
          <p className="mt-3 text-sm">{recommendation.message}</p>
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-lg font-semibold">{recommendation.suggested_paid_pct}%</div>
              <div className="text-xs text-ink-500">Paid Ads</div>
            </div>
            <div>
              <div className="text-lg font-semibold">{recommendation.suggested_influencer_pct}%</div>
              <div className="text-xs text-ink-500">Influencer Collabs</div>
            </div>
            <div>
              <div className="text-lg font-semibold">{recommendation.suggested_content_pct}%</div>
              <div className="text-xs text-ink-500">Content Production</div>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="mb-1 text-sm font-semibold text-ink-900">Log an Off-Platform Collaboration</h2>
        <p className="mb-4 text-xs text-ink-500">
          Booked a creator outside AdSaarthi? Log the cost here so it flows into your CAC tracking.
        </p>
        <form onSubmit={logCollaboration} className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {error && <div className="col-span-full rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
          <input
            className="input"
            placeholder="Creator name"
            required
            value={form.influencer_name}
            onChange={(e) => setForm({ ...form, influencer_name: e.target.value })}
          />
          <input
            className="input"
            placeholder="Cost (₹)"
            type="number"
            required
            value={form.cost}
            onChange={(e) => setForm({ ...form, cost: e.target.value })}
          />
          <input
            className="input"
            placeholder="Conversions attributed"
            type="number"
            value={form.conversions_attributed}
            onChange={(e) => setForm({ ...form, conversions_attributed: e.target.value })}
          />
          <input
            className="input"
            placeholder="Notes (optional)"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
          />
          <button type="submit" className="btn-primary col-span-full md:col-span-1">
            Log Collaboration
          </button>
        </form>
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Logged Collaborations</h2>
        {logs.length === 0 ? (
          <p className="text-sm text-ink-500">No off-platform collaborations logged yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-ink-500">
                <th className="pb-2">Creator</th>
                <th className="pb-2">Cost</th>
                <th className="pb-2">Conversions</th>
                <th className="pb-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className="border-t border-ink-100">
                  <td className="py-2 font-medium">{l.influencer_name}</td>
                  <td className="py-2">{formatCurrency(l.cost)}</td>
                  <td className="py-2">{l.conversions_attributed}</td>
                  <td className="py-2 text-ink-500">{l.notes || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
