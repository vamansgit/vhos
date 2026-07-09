import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/api/client";
import type { FinanceDashboard, TaxProfile } from "@/api/types";
import StatCard from "@/components/StatCard";
import { formatCurrency, formatDate } from "@/lib/format";

export default function Finance() {
  const [dashboard, setDashboard] = useState<FinanceDashboard | null>(null);
  const [taxProfile, setTaxProfile] = useState<TaxProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.get<FinanceDashboard>("/finance/dashboard?days=90"), api.get<TaxProfile>("/finance/tax-profile")]).then(
      ([d, t]) => {
        setDashboard(d);
        setTaxProfile(t);
        setLoading(false);
      }
    );
  }, []);

  if (loading || !dashboard) return <div className="p-8 text-ink-500">Loading…</div>;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">Finance & Compliance</h1>
        <p className="text-sm text-ink-500">Real-time, materialized from your sourcing and sales records — not a monthly close.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Revenue" value={formatCurrency(dashboard.revenue)} />
        <StatCard label="COGS" value={formatCurrency(dashboard.cogs)} />
        <StatCard
          label="Gross Margin"
          value={dashboard.gross_margin_pct !== null ? `${dashboard.gross_margin_pct}%` : "—"}
          tone={dashboard.gross_margin_pct !== null && dashboard.gross_margin_pct < 0 ? "negative" : "positive"}
        />
        <StatCard
          label="Net Profit"
          value={formatCurrency(dashboard.net_profit)}
          tone={dashboard.net_profit < 0 ? "negative" : "positive"}
        />
      </div>

      <div className="card">
        <h2 className="mb-4 text-sm font-semibold text-ink-900">Revenue vs COGS</h2>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={dashboard.daily_series}>
            <defs>
              <linearGradient id="revGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#6255cf" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#6255cf" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="cogsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#e11d48" stopOpacity={0.25} />
                <stop offset="100%" stopColor="#e11d48" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#eceef0" />
            <XAxis dataKey="date" tickFormatter={formatDate} tick={{ fontSize: 11, fill: "#697585" }} />
            <YAxis tick={{ fontSize: 11, fill: "#697585" }} width={50} />
            <Tooltip labelFormatter={(v) => formatDate(v as string)} formatter={(value: number) => formatCurrency(value)} />
            <Area type="monotone" dataKey="revenue" stroke="#6255cf" fill="url(#revGradient)" strokeWidth={2} />
            <Area type="monotone" dataKey="cogs" stroke="#e11d48" fill="url(#cogsGradient)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Tax Profile</h2>
        <p className="mb-3 text-xs text-ink-500">Pulled from your Onboard document vault — no re-entry needed.</p>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <div className="text-xs text-ink-500">GSTIN</div>
            <div className="font-medium">{taxProfile?.gstin ?? "Not registered yet"}</div>
          </div>
          <div>
            <div className="text-xs text-ink-500">Scheme</div>
            <div className="font-medium">{taxProfile?.applicable_schemes ?? "—"}</div>
          </div>
        </div>
        <p className="mt-3 text-xs text-ink-400">
          Nexus prepares and pre-fills compliance records — final review by you or your CA is required before filing.
        </p>
      </div>
    </div>
  );
}
