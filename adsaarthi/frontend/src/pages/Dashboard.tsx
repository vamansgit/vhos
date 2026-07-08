import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, ApiError } from "@/api/client";
import type { AdAccount, AdPlatform, DashboardSummary } from "@/api/types";
import StatCard from "@/components/StatCard";
import { formatCurrency, formatDate, formatNumber, titleCase } from "@/lib/format";

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [s, a] = await Promise.all([
        api.get<DashboardSummary>("/analytics/dashboard?days=90"),
        api.get<AdAccount[]>("/ad-accounts"),
      ]);
      setSummary(s);
      setAccounts(a);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function connectAccount(platform: AdPlatform) {
    setConnecting(true);
    try {
      await api.post("/ad-accounts", {
        platform,
        display_name: `${titleCase(platform)} Ads Account`,
      });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to connect account");
    } finally {
      setConnecting(false);
    }
  }

  if (loading) return <div className="text-ink-500">Loading dashboard…</div>;

  if (accounts.length === 0) {
    return (
      <div className="mx-auto max-w-lg text-center">
        <h1 className="text-xl font-semibold text-ink-900">Connect an ad account to get started</h1>
        <p className="mt-2 text-sm text-ink-500">
          Read-only OAuth connection — AdSaarthi never stores your ad account password (PRD 8.3).
        </p>
        <div className="card mt-6 flex flex-col gap-3">
          <button className="btn-primary" disabled={connecting} onClick={() => connectAccount("meta")}>
            Connect Meta (Instagram/Facebook) Ads
          </button>
          <button className="btn-secondary" disabled={connecting} onClick={() => connectAccount("youtube")}>
            Connect YouTube / Google Ads
          </button>
        </div>
        {error && <div className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
      </div>
    );
  }

  if (!summary) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-ink-900">Ad Performance Dashboard</h1>
          <p className="text-sm text-ink-500">Last 90 days, unified across {accounts.length} connected account(s).</p>
        </div>
        <div className="flex gap-2">
          {(["meta", "youtube"] as AdPlatform[])
            .filter((p) => !accounts.some((a) => a.platform === p))
            .map((p) => (
              <button key={p} className="btn-secondary" disabled={connecting} onClick={() => connectAccount(p)}>
                + Connect {titleCase(p)}
              </button>
            ))}
        </div>
      </div>

      {summary.trend_alert.triggered && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <strong>CAC alert:</strong> {summary.trend_alert.message}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total Spend" value={formatCurrency(summary.total_spend)} />
        <StatCard label="Conversions" value={formatNumber(summary.total_conversions)} />
        <StatCard
          label="Blended CAC"
          value={formatCurrency(summary.blended_cac)}
          tone={summary.trend_alert.triggered ? "negative" : "default"}
          hint={
            summary.trend_alert.change_pct !== null
              ? `${summary.trend_alert.change_pct > 0 ? "+" : ""}${summary.trend_alert.change_pct}% vs prior week`
              : undefined
          }
        />
        <StatCard label="Blended ROAS" value={summary.blended_roas ? `${summary.blended_roas}x` : "—"} tone="positive" />
      </div>

      <div className="card">
        <h2 className="mb-4 text-sm font-semibold text-ink-900">Spend & CAC Trend</h2>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={summary.daily_series}>
            <defs>
              <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#1eb371" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#1eb371" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#eceef0" />
            <XAxis dataKey="date" tickFormatter={formatDate} tick={{ fontSize: 11, fill: "#697585" }} />
            <YAxis tick={{ fontSize: 11, fill: "#697585" }} width={40} />
            <Tooltip
              labelFormatter={(v) => formatDate(v as string)}
              formatter={(value: number, name: string) => [
                name === "spend" ? formatCurrency(value) : value,
                name === "spend" ? "Spend" : name,
              ]}
            />
            <Area type="monotone" dataKey="spend" stroke="#1eb371" fill="url(#spendGradient)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-ink-900">By Platform</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-ink-500">
                <th className="pb-2">Platform</th>
                <th className="pb-2">Spend</th>
                <th className="pb-2">CAC</th>
              </tr>
            </thead>
            <tbody>
              {summary.by_platform.map((p) => (
                <tr key={p.platform} className="border-t border-ink-100">
                  <td className="py-2 font-medium">{titleCase(p.platform)}</td>
                  <td className="py-2">{formatCurrency(p.spend)}</td>
                  <td className="py-2">{formatCurrency(p.cac)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-ink-900">Category Benchmark</h2>
          {summary.benchmark ? (
            <div className="space-y-2 text-sm">
              <p className="text-ink-600">
                Compared to anonymized {summary.benchmark.category} brands on AdSaarthi:
              </p>
              <div className="flex justify-between">
                <span className="text-ink-500">Your CAC</span>
                <span className="font-medium">{formatCurrency(summary.benchmark.brand_cac)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-500">Category avg CAC</span>
                <span className="font-medium">{formatCurrency(summary.benchmark.avg_cac)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-500">Your ROAS</span>
                <span className="font-medium">{summary.benchmark.brand_roas ?? "—"}x</span>
              </div>
              <div className="flex justify-between">
                <span className="text-ink-500">Category avg ROAS</span>
                <span className="font-medium">{summary.benchmark.avg_roas}x</span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-ink-500">
              Not enough peer brands in your category yet — benchmark unlocks as more brands onboard.
            </p>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">By Campaign</h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase text-ink-500">
              <th className="pb-2">Campaign</th>
              <th className="pb-2">Platform</th>
              <th className="pb-2">Spend</th>
              <th className="pb-2">Conversions</th>
              <th className="pb-2">CAC</th>
              <th className="pb-2">ROAS</th>
            </tr>
          </thead>
          <tbody>
            {summary.by_campaign.map((c) => (
              <tr key={`${c.campaign_name}-${c.platform}`} className="border-t border-ink-100">
                <td className="py-2 font-medium">{c.campaign_name}</td>
                <td className="py-2">{titleCase(c.platform)}</td>
                <td className="py-2">{formatCurrency(c.spend)}</td>
                <td className="py-2">{formatNumber(c.conversions)}</td>
                <td className="py-2">{formatCurrency(c.cac)}</td>
                <td className="py-2">{c.roas ? `${c.roas}x` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
