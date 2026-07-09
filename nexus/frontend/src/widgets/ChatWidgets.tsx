import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import type { FinanceDashboard, SourcingMatch, Store } from "@/api/types";
import { formatCurrency } from "@/lib/format";

export function SourceMatchWidget({ sourcingRequestId }: { sourcingRequestId: string }) {
  const [matches, setMatches] = useState<SourcingMatch[] | null>(null);

  useEffect(() => {
    api.get<SourcingMatch[]>(`/source/requests/${sourcingRequestId}/matches`).then(setMatches);
  }, [sourcingRequestId]);

  if (!matches) return null;

  return (
    <div className="mt-3 space-y-2">
      {matches.slice(0, 3).map((m) => (
        <div key={m.id} className="flex items-center justify-between rounded-lg border border-ink-100 bg-ink-50 px-3 py-2 text-sm">
          <div>
            <div className="font-medium text-ink-900">{m.supplier.name}</div>
            <div className="text-xs text-ink-500">{m.reason}</div>
          </div>
          <div className="text-right">
            <div className="font-semibold text-brand-700">{formatCurrency(m.estimated_unit_price)}/unit</div>
            <div className="text-xs text-ink-500">Fit {m.fit_score}/100</div>
          </div>
        </div>
      ))}
      <Link to={`/source/${sourcingRequestId}`} className="inline-block text-xs font-medium text-brand-700 hover:underline">
        View all matches & send RFQs →
      </Link>
    </div>
  );
}

export function FinanceWidget({ payload }: { payload: Partial<FinanceDashboard> }) {
  return (
    <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
      {[
        ["Revenue", formatCurrency(payload.revenue)],
        ["COGS", formatCurrency(payload.cogs)],
        ["Margin", payload.gross_margin_pct !== null && payload.gross_margin_pct !== undefined ? `${payload.gross_margin_pct}%` : "—"],
        ["Net", formatCurrency(payload.net_profit)],
      ].map(([label, value]) => (
        <div key={label} className="rounded-lg border border-ink-100 bg-ink-50 px-3 py-2 text-center">
          <div className="text-xs text-ink-500">{label}</div>
          <div className="text-sm font-semibold text-ink-900">{value}</div>
        </div>
      ))}
      <Link to="/finance" className="col-span-full text-xs font-medium text-brand-700 hover:underline">
        Open Finance dashboard →
      </Link>
    </div>
  );
}

export function SellWidget({ storeId }: { storeId: string }) {
  const [store, setStore] = useState<Store | null>(null);

  useEffect(() => {
    api.get<Store>("/sell/store").then(setStore);
  }, [storeId]);

  if (!store) return null;

  return (
    <div className="mt-3 flex items-center gap-3 rounded-lg border border-ink-100 bg-ink-50 px-3 py-2">
      <div
        className="h-8 w-8 flex-shrink-0 rounded-md"
        style={{ backgroundColor: store.theme_config.palette?.primary ?? "#6255cf" }}
      />
      <div className="text-sm">
        <div className="font-medium text-ink-900">{store.domain}</div>
        <div className="text-xs text-ink-500">{store.theme_config.tagline}</div>
      </div>
      <Link to="/sell" className="ml-auto text-xs font-medium text-brand-700 hover:underline">
        Open Sell →
      </Link>
    </div>
  );
}

export function OnboardWidget({ payload }: { payload: Record<string, unknown> }) {
  if (payload.target_geographies) {
    return (
      <div className="mt-3 rounded-lg border border-ink-100 bg-ink-50 px-3 py-2 text-sm">
        <span className="text-ink-500">Target geographies:</span>{" "}
        <span className="font-medium text-ink-900">{String(payload.target_geographies)}</span>
      </div>
    );
  }
  return (
    <Link to="/onboard" className="mt-3 inline-block text-xs font-medium text-brand-700 hover:underline">
      Open Onboard →
    </Link>
  );
}
