import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { PaymentProvider, Product, SourcedOrder, ShippingZone, Store, StoreOrder } from "@/api/types";
import { formatCurrency, formatDate, formatNumber, titleCase } from "@/lib/format";

export default function Sell() {
  const [store, setStore] = useState<Store | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [providers, setProviders] = useState<PaymentProvider[]>([]);
  const [zones, setZones] = useState<ShippingZone[]>([]);
  const [orders, setOrders] = useState<StoreOrder[]>([]);
  const [sourcedOrders, setSourcedOrders] = useState<SourcedOrder[]>([]);
  const [markup, setMarkup] = useState("2.0");
  const [selectedSourcedOrder, setSelectedSourcedOrder] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    let currentStore: Store;
    try {
      currentStore = await api.get<Store>("/sell/store");
    } catch {
      currentStore = await api.post<Store>("/sell/store");
    }
    setStore(currentStore);
    const [p, prov, z, o, so] = await Promise.all([
      api.get<Product[]>("/sell/products"),
      api.get<PaymentProvider[]>("/sell/payment-providers"),
      api.get<ShippingZone[]>("/sell/shipping-zones"),
      api.get<StoreOrder[]>("/sell/orders"),
      api.get<SourcedOrder[]>("/source/orders"),
    ]);
    setProducts(p);
    setProviders(prov);
    setZones(z);
    setOrders(o);
    setSourcedOrders(so);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function addFromSourcedOrder(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedSourcedOrder) return;
    await api.post("/sell/products/from-sourced-order", {
      sourced_order_id: selectedSourcedOrder,
      markup_multiplier: Number(markup),
    });
    setProducts(await api.get<Product[]>("/sell/products"));
  }

  async function activateProvider(id: string) {
    await api.post(`/sell/payment-providers/${id}/activate`);
    setProviders(await api.get<PaymentProvider[]>("/sell/payment-providers"));
  }

  async function generateDemoOrders() {
    await api.post("/sell/demo-orders");
    setOrders(await api.get<StoreOrder[]>("/sell/orders"));
  }

  if (loading || !store) return <div className="p-8 text-ink-500">Loading…</div>;

  const availableSourcedOrders = sourcedOrders.filter((so) => !products.some((p) => p.sourced_order_id === so.id));

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <div className="card">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg" style={{ backgroundColor: store.theme_config.palette?.primary ?? "#6255cf" }} />
          <div>
            <h1 className="text-lg font-semibold text-ink-900">{store.domain}</h1>
            <p className="text-sm text-ink-500">{store.theme_config.tagline}</p>
          </div>
          <span className="badge ml-auto bg-ink-100 text-ink-600">{store.published ? "Published" : "Draft"}</span>
        </div>
        <div className="mt-3 flex flex-wrap gap-1">
          {store.pages.map((p) => (
            <span key={p.slug} className="badge bg-brand-50 text-brand-700">{p.title}</span>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Catalog</h2>
        {products.length === 0 ? (
          <p className="text-sm text-ink-500">No products yet — pull in a sourced item below.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-ink-500">
                <th className="pb-2">Product</th>
                <th className="pb-2">Price</th>
                <th className="pb-2">Cost</th>
                <th className="pb-2">Inventory</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr key={p.id} className="border-t border-ink-100">
                  <td className="py-2 font-medium">{p.title}</td>
                  <td className="py-2">{formatCurrency(p.price)}</td>
                  <td className="py-2">{formatCurrency(p.cost_basis)}</td>
                  <td className="py-2">{formatNumber(p.inventory)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {availableSourcedOrders.length > 0 && (
          <form onSubmit={addFromSourcedOrder} className="mt-4 flex flex-wrap items-center gap-2 border-t border-ink-100 pt-4">
            <select className="input flex-1" value={selectedSourcedOrder} onChange={(e) => setSelectedSourcedOrder(e.target.value)}>
              <option value="">Select a sourced item…</option>
              {availableSourcedOrders.map((so) => (
                <option key={so.id} value={so.id}>{so.title} ({formatCurrency(so.unit_cost)}/unit)</option>
              ))}
            </select>
            <input className="input w-28" type="number" step="0.1" value={markup} onChange={(e) => setMarkup(e.target.value)} placeholder="Markup x" />
            <button type="submit" className="btn-primary">Add to Catalog</button>
          </form>
        )}
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Payments — pre-enabled by default</h2>
        <div className="space-y-2">
          {providers.map((p) => (
            <div key={p.id} className="flex items-center justify-between border-t border-ink-100 py-2 text-sm first:border-t-0">
              <div className="font-medium">{titleCase(p.provider)}</div>
              <div className="flex items-center gap-2">
                <span className="badge bg-ink-100 text-ink-600">{titleCase(p.status)}</span>
                {p.status === "pre_enabled" && (
                  <button className="btn-secondary" onClick={() => activateProvider(p.id)}>Confirm & Activate</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Shipping Zones</h2>
        <div className="space-y-2 text-sm">
          {zones.map((z) => (
            <div key={z.id} className="flex justify-between border-t border-ink-100 py-2 first:border-t-0">
              <span>{z.region}</span>
              <span className="text-ink-500">{z.carrier}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-ink-900">Orders</h2>
          <button className="btn-secondary" onClick={generateDemoOrders}>Generate Demo Orders</button>
        </div>
        {orders.length === 0 ? (
          <p className="text-sm text-ink-500">No orders yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-ink-500">
                <th className="pb-2">Date</th>
                <th className="pb-2">Items</th>
                <th className="pb-2">Subtotal</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.slice(0, 15).map((o) => (
                <tr key={o.id} className="border-t border-ink-100">
                  <td className="py-2">{formatDate(o.created_at)}</td>
                  <td className="py-2">{o.line_items.map((li) => li.title).join(", ")}</td>
                  <td className="py-2">{formatCurrency(o.subtotal)}</td>
                  <td className="py-2">{titleCase(o.fulfillment_status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
