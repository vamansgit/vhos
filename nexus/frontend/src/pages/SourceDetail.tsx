import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "@/api/client";
import type { RFQ, SourcedOrder, SourcingMatch, SourcingRequest } from "@/api/types";
import { formatCurrency, formatNumber, titleCase } from "@/lib/format";

export default function SourceDetail() {
  const { id } = useParams<{ id: string }>();
  const [request, setRequest] = useState<SourcingRequest | null>(null);
  const [matches, setMatches] = useState<SourcingMatch[]>([]);
  const [rfqs, setRfqs] = useState<RFQ[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [quoteForms, setQuoteForms] = useState<Record<string, { unit_price: string; lead_time_days: string }>>({});
  const [quotes, setQuotes] = useState<Record<string, { id: string; unit_price: number }>>({});
  const [acceptedOrder, setAcceptedOrder] = useState<SourcedOrder | null>(null);
  const [loading, setLoading] = useState(true);
  const [matching, setMatching] = useState(false);

  async function load() {
    if (!id) return;
    const [req, m, r] = await Promise.all([
      api.get<SourcingRequest>(`/source/requests/${id}`),
      api.get<SourcingMatch[]>(`/source/requests/${id}/matches`),
      api.get<RFQ[]>(`/source/requests/${id}/rfqs`),
    ]);
    setRequest(req);
    setMatches(m);
    setRfqs(r);
    setQuotes((prev) => {
      const fromServer = Object.fromEntries(
        r.filter((rfq) => rfq.quote).map((rfq) => [rfq.id, { id: rfq.quote!.id, unit_price: rfq.quote!.unit_price }])
      );
      return { ...fromServer, ...prev };
    });
    setLoading(false);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function runMatch() {
    if (!id) return;
    setMatching(true);
    try {
      const m = await api.post<SourcingMatch[]>(`/source/requests/${id}/match`);
      setMatches(m);
    } finally {
      setMatching(false);
    }
  }

  function toggleSelected(supplierId: string) {
    setSelected((prev) => (prev.includes(supplierId) ? prev.filter((s) => s !== supplierId) : [...prev, supplierId]));
  }

  async function sendRfqs() {
    if (!id || selected.length === 0) return;
    const created = await api.post<RFQ[]>(`/source/requests/${id}/rfqs`, { supplier_ids: selected });
    setRfqs((prev) => [...prev, ...created]);
    setSelected([]);
  }

  async function submitQuote(rfqId: string) {
    const form = quoteForms[rfqId];
    if (!form?.unit_price) return;
    const quote = await api.post<{ id: string; unit_price: number }>(`/source/rfqs/${rfqId}/quote`, {
      unit_price: Number(form.unit_price),
      moq: request?.quantity ?? 1,
      lead_time_days: Number(form.lead_time_days || 14),
    });
    setQuotes((prev) => ({ ...prev, [rfqId]: quote }));
  }

  async function acceptQuote(rfqId: string) {
    const quote = quotes[rfqId];
    if (!quote || !request?.quantity) return;
    const order = await api.post<SourcedOrder>(`/source/quotes/${quote.id}/accept`, { quantity: request.quantity });
    setAcceptedOrder(order);
  }

  if (loading || !request) return <div className="p-8 text-ink-500">Loading…</div>;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">{request.raw_text}</h1>
        <p className="text-sm text-ink-500">
          {titleCase(request.category)}
          {request.quantity ? ` · ${formatNumber(request.quantity)} units` : ""}
          {request.destination ? ` · to ${request.destination}` : ""}
        </p>
      </div>

      {acceptedOrder && (
        <div className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          Order accepted: {formatNumber(acceptedOrder.quantity)} units at {formatCurrency(acceptedOrder.unit_cost)}/unit
          (total {formatCurrency(acceptedOrder.total_cost)}). Head to Sell to add it to your catalog.
        </div>
      )}

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-ink-900">Ranked Matches</h2>
          <button className="btn-secondary" onClick={runMatch} disabled={matching}>
            {matching ? "Matching…" : matches.length > 0 ? "Re-run Match" : "Run Match"}
          </button>
        </div>
        <div className="space-y-3">
          {matches.map((m) => (
            <div key={m.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  <input type="checkbox" className="mt-1" checked={selected.includes(m.supplier.id)} onChange={() => toggleSelected(m.supplier.id)} />
                  <div>
                    <div className="font-semibold text-ink-900">{m.supplier.name}</div>
                    <div className="text-xs text-ink-500">{m.supplier.location} · {titleCase(m.supplier.verification_status)}</div>
                    <p className="mt-1 text-sm text-ink-600">{m.reason}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-semibold text-brand-700">{m.fit_score}/100</div>
                  <div className="text-xs text-ink-500">{formatCurrency(m.estimated_unit_price)}/unit</div>
                </div>
              </div>
            </div>
          ))}
          {matches.length === 0 && <p className="text-sm text-ink-500">No matches yet — run match to see ranked suppliers.</p>}
        </div>
        {selected.length > 0 && (
          <button className="btn-primary mt-3" onClick={sendRfqs}>
            Send RFQ to {selected.length} supplier{selected.length > 1 ? "s" : ""}
          </button>
        )}
      </div>

      {rfqs.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold text-ink-900">RFQs</h2>
          <div className="space-y-3">
            {rfqs.map((rfq) => (
              <div key={rfq.id} className="card">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-ink-900">{rfq.supplier.name}</div>
                  <span className="badge bg-ink-100 text-ink-600">{titleCase(rfq.status)}</span>
                </div>
                <pre className="mt-2 whitespace-pre-wrap font-sans text-xs text-ink-500">{rfq.message}</pre>

                {quotes[rfq.id] ? (
                  <div className="mt-3 flex items-center justify-between border-t border-ink-100 pt-3 text-sm">
                    <span>Quoted at {formatCurrency(quotes[rfq.id].unit_price)}/unit</span>
                    <button className="btn-primary" onClick={() => acceptQuote(rfq.id)} disabled={!!acceptedOrder}>
                      Accept Quote
                    </button>
                  </div>
                ) : rfq.status === "open" ? (
                  <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-ink-100 pt-3">
                    <input
                      className="input w-32"
                      placeholder="Quoted ₹/unit"
                      type="number"
                      value={quoteForms[rfq.id]?.unit_price ?? ""}
                      onChange={(e) => setQuoteForms((prev) => ({ ...prev, [rfq.id]: { ...prev[rfq.id], unit_price: e.target.value } }))}
                    />
                    <input
                      className="input w-36"
                      placeholder="Lead time (days)"
                      type="number"
                      value={quoteForms[rfq.id]?.lead_time_days ?? ""}
                      onChange={(e) => setQuoteForms((prev) => ({ ...prev, [rfq.id]: { ...prev[rfq.id], lead_time_days: e.target.value } }))}
                    />
                    <button className="btn-secondary" onClick={() => submitQuote(rfq.id)}>
                      Log Supplier's Quote
                    </button>
                  </div>
                ) : (
                  <div className="mt-3 border-t border-ink-100 pt-3 text-xs text-ink-500">
                    This RFQ is {rfq.status} — no quote on file.
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
