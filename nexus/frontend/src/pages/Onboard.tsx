import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { Brand, ChecklistItem, DocumentOut, FounderProfile } from "@/api/types";
import { useAuth } from "@/state/auth";
import { formatDate, titleCase } from "@/lib/format";

const DOC_TYPES = ["incorporation", "gst", "fssai", "bis", "iec", "trademark", "labour", "bank_kyc", "other"];

const STATUS_STYLES: Record<string, string> = {
  missing: "bg-ink-100 text-ink-600",
  uploaded: "bg-brand-100 text-brand-800",
  verified: "bg-green-100 text-green-800",
  expiring_soon: "bg-amber-100 text-amber-800",
  expired: "bg-red-100 text-red-700",
};

export default function Onboard() {
  const { refreshBrand } = useAuth();
  const [brand, setBrand] = useState<Brand | null>(null);
  const [founder, setFounder] = useState<FounderProfile | null>(null);
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [docForm, setDocForm] = useState({ type: "gst", label: "", file_ref: "", extracted_value: "" });
  const [loading, setLoading] = useState(true);

  async function load() {
    const [b, f, d, c] = await Promise.all([
      api.get<Brand>("/onboard/brand"),
      api.get<FounderProfile>("/onboard/founder"),
      api.get<DocumentOut[]>("/onboard/documents"),
      api.get<ChecklistItem[]>("/onboard/checklist"),
    ]);
    setBrand(b);
    setFounder(f);
    setDocuments(d);
    setChecklist(c);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  async function saveBrand(e: React.FormEvent) {
    e.preventDefault();
    if (!brand) return;
    const updated = await api.patch<Brand>("/onboard/brand", {
      category: brand.category,
      stage: brand.stage,
      structure: brand.structure,
      target_geographies: brand.target_geographies,
      style_descriptors: brand.style_descriptors,
      team_size: brand.team_size,
    });
    setBrand(updated);
    await refreshBrand();
  }

  async function saveFounder(e: React.FormEvent) {
    e.preventDefault();
    if (!founder) return;
    const updated = await api.patch<FounderProfile>("/onboard/founder", founder);
    setFounder(updated);
  }

  async function uploadDocument(e: React.FormEvent) {
    e.preventDefault();
    await api.post("/onboard/documents", {
      type: docForm.type,
      label: docForm.label || titleCase(docForm.type),
      file_ref: docForm.file_ref || `vault/${docForm.type}-${Date.now()}.pdf`,
      extracted_value: docForm.extracted_value || null,
    });
    setDocForm({ type: "gst", label: "", file_ref: "", extracted_value: "" });
    setDocuments(await api.get<DocumentOut[]>("/onboard/documents"));
  }

  async function toggleChecklistItem(item: ChecklistItem) {
    const nextStatus = item.status === "done" ? "not_started" : "done";
    const updated = await api.patch<ChecklistItem>(`/onboard/checklist/${item.id}`, { status: nextStatus });
    setChecklist((prev) => prev.map((c) => (c.id === item.id ? updated : c)));
  }

  if (loading || !brand || !founder) return <div className="p-8 text-ink-500">Loading…</div>;

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-8">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">Onboard</h1>
        <p className="text-sm text-ink-500">Your brand profile, founder background, and document vault — the seed data every other module reads from.</p>
      </div>

      <form onSubmit={saveBrand} className="card space-y-4">
        <h2 className="text-sm font-semibold text-ink-900">Brand Profile</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Category</label>
            <input className="input" value={brand.category ?? ""} onChange={(e) => setBrand({ ...brand, category: e.target.value })} />
          </div>
          <div>
            <label className="label">Stage</label>
            <select className="input" value={brand.stage} onChange={(e) => setBrand({ ...brand, stage: e.target.value as Brand["stage"] })}>
              <option value="idea">Idea</option>
              <option value="pre_launch">Pre-launch</option>
              <option value="live">Live</option>
            </select>
          </div>
          <div>
            <label className="label">Business structure</label>
            <select className="input" value={brand.structure} onChange={(e) => setBrand({ ...brand, structure: e.target.value as Brand["structure"] })}>
              <option value="not_incorporated">Not incorporated yet</option>
              <option value="proprietorship">Proprietorship</option>
              <option value="llp">LLP</option>
              <option value="pvt_ltd">Pvt Ltd</option>
            </select>
          </div>
          <div>
            <label className="label">Team size</label>
            <input className="input" type="number" min={1} value={brand.team_size} onChange={(e) => setBrand({ ...brand, team_size: Number(e.target.value) })} />
          </div>
        </div>
        <div>
          <label className="label">Target geographies</label>
          <input className="input" value={brand.target_geographies ?? ""} onChange={(e) => setBrand({ ...brand, target_geographies: e.target.value })} placeholder="India, US, UK" />
        </div>
        <div>
          <label className="label">Style descriptors</label>
          <input className="input" value={brand.style_descriptors ?? ""} onChange={(e) => setBrand({ ...brand, style_descriptors: e.target.value })} placeholder="minimal, earthy" />
        </div>
        <button type="submit" className="btn-primary">Save Brand Profile</button>
      </form>

      <form onSubmit={saveFounder} className="card space-y-4">
        <h2 className="text-sm font-semibold text-ink-900">Founder Profile</h2>
        <div>
          <label className="label">Background</label>
          <textarea className="input" rows={2} value={founder.background_text ?? ""} onChange={(e) => setFounder({ ...founder, background_text: e.target.value })} />
        </div>
        <div>
          <label className="label">Aspirations</label>
          <textarea className="input" rows={2} value={founder.aspirations_text ?? ""} onChange={(e) => setFounder({ ...founder, aspirations_text: e.target.value })} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Risk appetite</label>
            <select className="input" value={founder.risk_appetite ?? "medium"} onChange={(e) => setFounder({ ...founder, risk_appetite: e.target.value })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label className="label">Hours/week available</label>
            <input className="input" type="number" min={1} value={founder.time_availability_hours_per_week ?? ""} onChange={(e) => setFounder({ ...founder, time_availability_hours_per_week: Number(e.target.value) })} />
          </div>
        </div>
        <button type="submit" className="btn-primary">Save Founder Profile</button>
      </form>

      <div className="card">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Guided Checklist</h2>
        <div className="space-y-2">
          {checklist.map((item) => (
            <label key={item.id} className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-0.5" checked={item.status === "done"} onChange={() => toggleChecklistItem(item)} />
              <span>
                <span className={item.status === "done" ? "text-ink-400 line-through" : "text-ink-800"}>{item.requirement}</span>
                {item.due_context && <span className="block text-xs text-ink-500">{item.due_context}</span>}
              </span>
            </label>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="mb-1 text-sm font-semibold text-ink-900">Document Vault</h2>
        <p className="mb-4 text-xs text-ink-500">Add, update, and version company documents — the source of truth for Finance & Compliance.</p>

        <div className="space-y-2">
          {documents.map((doc) => (
            <div key={doc.id} className="flex items-center justify-between border-t border-ink-100 py-2 text-sm first:border-t-0">
              <div>
                <div className="font-medium">{doc.label}</div>
                <div className="text-xs text-ink-500">
                  {titleCase(doc.type)} · v{doc.versions.length} · expires {formatDate(doc.expiry_date)}
                </div>
              </div>
              <span className={`badge ${STATUS_STYLES[doc.status] ?? "bg-ink-100"}`}>{titleCase(doc.status)}</span>
            </div>
          ))}
          {documents.length === 0 && <p className="text-sm text-ink-500">No documents uploaded yet.</p>}
        </div>

        <form onSubmit={uploadDocument} className="mt-4 grid grid-cols-2 gap-3 border-t border-ink-100 pt-4 md:grid-cols-4">
          <select className="input" value={docForm.type} onChange={(e) => setDocForm({ ...docForm, type: e.target.value })}>
            {DOC_TYPES.map((t) => (
              <option key={t} value={t}>{titleCase(t)}</option>
            ))}
          </select>
          <input className="input" placeholder="Label" value={docForm.label} onChange={(e) => setDocForm({ ...docForm, label: e.target.value })} />
          <input className="input" placeholder="Extracted value (e.g. GSTIN)" value={docForm.extracted_value} onChange={(e) => setDocForm({ ...docForm, extracted_value: e.target.value })} />
          <button type="submit" className="btn-primary">Add / Update</button>
        </form>
        <p className="mt-2 text-xs text-ink-400">Demo uploads a file reference only — swap in real object storage for production.</p>
      </div>
    </div>
  );
}
