import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/api/client";
import type { SourcedOrder, SourcingRequest } from "@/api/types";
import { formatCurrency, formatNumber, titleCase } from "@/lib/format";

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-ink-100 text-ink-600",
  matching: "bg-amber-100 text-amber-800",
  matched: "bg-brand-100 text-brand-800",
  rfq_sent: "bg-blue-100 text-blue-800",
  quoted: "bg-blue-100 text-blue-800",
  accepted: "bg-green-100 text-green-800",
};

export default function SourceList() {
  const [requests, setRequests] = useState<SourcingRequest[]>([]);
  const [orders, setOrders] = useState<SourcedOrder[]>([]);
  const [rawText, setRawText] = useState("");
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    const [r, o] = await Promise.all([
      api.get<SourcingRequest[]>("/source/requests"),
      api.get<SourcedOrder[]>("/source/orders"),
    ]);
    setRequests(r);
    setOrders(o);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function createRequest(e: React.FormEvent) {
    e.preventDefault();
    if (!rawText.trim()) return;
    setCreating(true);
    try {
      await api.post("/source/requests", { raw_text: rawText });
      setRawText("");
      await load();
    } finally {
      setCreating(false);
    }
  }

  if (loading) return <div className="p-8 text-ink-500">Loading…</div>;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">Source</h1>
        <p className="text-sm text-ink-500">Describe what you need — products, packaging, or logistics — and get a ranked supplier shortlist.</p>
      </div>

      <form onSubmit={createRequest} className="card space-y-3">
        <label className="label">New sourcing request</label>
        <textarea
          className="input"
          rows={2}
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
          placeholder="I need 1,000 amber glass dropper bottles, 30ml, delivered to Mumbai in 3 weeks, budget under ₹15/unit."
        />
        <button type="submit" className="btn-primary" disabled={creating}>
          {creating ? "Searching…" : "Find Suppliers"}
        </button>
      </form>

      {orders.length > 0 && (
        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-ink-900">Accepted Sourced Orders</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-ink-500">
                <th className="pb-2">Item</th>
                <th className="pb-2">Qty</th>
                <th className="pb-2">Unit Cost</th>
                <th className="pb-2">Total</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-t border-ink-100">
                  <td className="py-2 font-medium">{o.title}</td>
                  <td className="py-2">{formatNumber(o.quantity)}</td>
                  <td className="py-2">{formatCurrency(o.unit_cost)}</td>
                  <td className="py-2">{formatCurrency(o.total_cost)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="space-y-3">
        {requests.map((r) => (
          <Link key={r.id} to={`/source/${r.id}`} className="card block hover:border-brand-300">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-medium text-ink-900">{r.raw_text}</div>
                <div className="mt-1 text-xs text-ink-500">
                  {titleCase(r.category)}
                  {r.quantity ? ` · ${formatNumber(r.quantity)} units` : ""}
                  {r.target_price ? ` · under ${formatCurrency(r.target_price)}` : ""}
                </div>
              </div>
              <span className={`badge ${STATUS_STYLES[r.status] ?? "bg-ink-100"}`}>{titleCase(r.status)}</span>
            </div>
          </Link>
        ))}
        {requests.length === 0 && <p className="text-sm text-ink-500">No sourcing requests yet.</p>}
      </div>
    </div>
  );
}
