import { useEffect, useState } from "react";
import { api, ApiError } from "@/api/client";
import type { AdAccount, User, UserRole } from "@/api/types";
import { useAuth } from "@/state/auth";
import { titleCase } from "@/lib/format";

const CATEGORIES = ["beauty", "fashion", "wellness", "food", "tech", "home", "fitness", "parenting", "finance", "travel"];

export default function Settings() {
  const { brand, user, refreshBrand } = useAuth();
  const [form, setForm] = useState({
    category: brand?.category ?? "wellness",
    target_audience: brand?.target_audience ?? "",
    brand_voice: brand?.brand_voice ?? "",
    cac_alert_threshold_pct: brand?.cac_alert_threshold_pct ?? 15,
  });
  const [accounts, setAccounts] = useState<AdAccount[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [inviteForm, setInviteForm] = useState({ email: "", full_name: "", password: "", role: "marketer" as UserRole });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (brand) {
      setForm({
        category: brand.category ?? "wellness",
        target_audience: brand.target_audience ?? "",
        brand_voice: brand.brand_voice ?? "",
        cac_alert_threshold_pct: brand.cac_alert_threshold_pct,
      });
    }
  }, [brand]);

  useEffect(() => {
    api.get<AdAccount[]>("/ad-accounts").then(setAccounts);
    api.get<User[]>("/brands/me/users").then(setUsers);
  }, []);

  async function saveBrand(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      await api.patch("/brands/me", form);
      await refreshBrand();
      setMessage("Brand settings saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function syncAccount(id: string) {
    await api.post(`/ad-accounts/${id}/sync`);
    setAccounts(await api.get<AdAccount[]>("/ad-accounts"));
  }

  async function disconnectAccount(id: string) {
    await api.delete(`/ad-accounts/${id}`);
    setAccounts(await api.get<AdAccount[]>("/ad-accounts"));
  }

  async function inviteUser(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/brands/me/users", inviteForm);
      setInviteForm({ email: "", full_name: "", password: "", role: "marketer" });
      setUsers(await api.get<User[]>("/brands/me/users"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to invite user");
    }
  }

  const isOwner = user?.role === "owner";

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">Settings</h1>
        <p className="text-sm text-ink-500">Brand voice, alert thresholds, connected accounts, and team roles.</p>
      </div>

      <form onSubmit={saveBrand} className="card space-y-4">
        <h2 className="text-sm font-semibold text-ink-900">Brand Profile</h2>
        {message && <div className="rounded-lg bg-brand-50 px-3 py-2 text-sm text-brand-700">{message}</div>}
        {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        <div>
          <label className="label">Category</label>
          <select className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {titleCase(c)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Target audience</label>
          <input className="input" value={form.target_audience} onChange={(e) => setForm({ ...form, target_audience: e.target.value })} />
        </div>
        <div>
          <label className="label">Brand voice</label>
          <textarea className="input" rows={2} value={form.brand_voice} onChange={(e) => setForm({ ...form, brand_voice: e.target.value })} placeholder="warm, encouraging, jargon-free" />
        </div>
        <div>
          <label className="label">CAC alert threshold (%)</label>
          <input
            className="input w-32"
            type="number"
            min={0}
            max={100}
            value={form.cac_alert_threshold_pct}
            onChange={(e) => setForm({ ...form, cac_alert_threshold_pct: Number(e.target.value) })}
          />
        </div>
        <button type="submit" className="btn-primary" disabled={saving || !isOwner}>
          {saving ? "Saving…" : "Save"}
        </button>
        {!isOwner && <p className="text-xs text-ink-500">Only the brand owner can edit these settings.</p>}
      </form>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Connected Ad Accounts</h2>
        {accounts.length === 0 ? (
          <p className="text-sm text-ink-500">No accounts connected yet — connect one from the Dashboard.</p>
        ) : (
          <div className="space-y-2">
            {accounts.map((a) => (
              <div key={a.id} className="flex items-center justify-between border-t border-ink-100 py-2 text-sm first:border-t-0">
                <div>
                  <div className="font-medium">{a.display_name}</div>
                  <div className="text-xs text-ink-500">
                    {titleCase(a.platform)} · {a.status} · last synced {a.last_synced_at ? new Date(a.last_synced_at).toLocaleString() : "never"}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button className="btn-secondary" onClick={() => syncAccount(a.id)}>
                    Re-sync
                  </button>
                  <button className="btn-danger" onClick={() => disconnectAccount(a.id)}>
                    Disconnect
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Team</h2>
        <div className="space-y-2">
          {users.map((u) => (
            <div key={u.id} className="flex items-center justify-between border-t border-ink-100 py-2 text-sm first:border-t-0">
              <div>
                <div className="font-medium">{u.full_name}</div>
                <div className="text-xs text-ink-500">{u.email}</div>
              </div>
              <span className="badge bg-ink-100 text-ink-700">{titleCase(u.role)}</span>
            </div>
          ))}
        </div>

        {isOwner && (
          <form onSubmit={inviteUser} className="mt-4 grid grid-cols-2 gap-3 border-t border-ink-100 pt-4 md:grid-cols-4">
            <input className="input" placeholder="Name" required value={inviteForm.full_name} onChange={(e) => setInviteForm({ ...inviteForm, full_name: e.target.value })} />
            <input className="input" placeholder="Email" type="email" required value={inviteForm.email} onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })} />
            <input className="input" placeholder="Temp password" required minLength={8} value={inviteForm.password} onChange={(e) => setInviteForm({ ...inviteForm, password: e.target.value })} />
            <select className="input" value={inviteForm.role} onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value as UserRole })}>
              <option value="marketer">Marketer</option>
              <option value="content_manager">Content Manager</option>
              <option value="owner">Owner</option>
            </select>
            <button type="submit" className="btn-primary col-span-full md:col-span-1">
              Invite
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
