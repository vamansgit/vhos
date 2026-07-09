import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "@/api/client";
import type { CampaignBrief, CampaignObjective, ContentFormat } from "@/api/types";

const OBJECTIVES: { value: CampaignObjective; label: string }[] = [
  { value: "awareness", label: "Awareness" },
  { value: "launch", label: "Product Launch" },
  { value: "sales", label: "Sales" },
  { value: "retargeting", label: "Retargeting" },
  { value: "influencer_collab", label: "Influencer Collab" },
];

const FORMATS: { value: ContentFormat; label: string }[] = [
  { value: "reels", label: "Instagram Reels" },
  { value: "static_post", label: "Static Post" },
  { value: "youtube_shorts", label: "YouTube Shorts" },
  { value: "youtube_long_form", label: "YouTube Long-form" },
];

export default function CampaignBriefBuilder() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    objective: "launch" as CampaignObjective,
    target_audience_age: "",
    target_audience_gender: "",
    target_audience_geography: "",
    target_audience_interests: "",
    desired_reach: "",
    content_format: "reels" as ContentFormat,
    total_budget: "",
    notes: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const brief = await api.post<CampaignBrief>("/campaigns", {
        ...form,
        desired_reach: form.desired_reach ? Number(form.desired_reach) : null,
        total_budget: Number(form.total_budget),
      });
      navigate(`/campaigns/${brief.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create campaign brief");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">New Campaign Brief</h1>
        <p className="text-sm text-ink-500">
          Step 1 of the Auto-Match flow — describe what you need, and AdSaarthi ranks creators, recommends bids, and
          drafts content for you.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-4">
        {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Objective</label>
            <select className="input" value={form.objective} onChange={(e) => update("objective", e.target.value as CampaignObjective)}>
              {OBJECTIVES.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Content Format</label>
            <select className="input" value={form.content_format} onChange={(e) => update("content_format", e.target.value as ContentFormat)}>
              {FORMATS.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Target age</label>
            <input className="input" placeholder="22-35" value={form.target_audience_age} onChange={(e) => update("target_audience_age", e.target.value)} />
          </div>
          <div>
            <label className="label">Target gender</label>
            <input className="input" placeholder="female / male / all" value={form.target_audience_gender} onChange={(e) => update("target_audience_gender", e.target.value)} />
          </div>
        </div>

        <div>
          <label className="label">Target geography</label>
          <input className="input" placeholder="India, Tier 1 & 2 cities" value={form.target_audience_geography} onChange={(e) => update("target_audience_geography", e.target.value)} />
        </div>

        <div>
          <label className="label">Target interests / category keywords</label>
          <input className="input" placeholder="wellness, skincare, self-care" value={form.target_audience_interests} onChange={(e) => update("target_audience_interests", e.target.value)} />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Desired reach (optional)</label>
            <input className="input" type="number" value={form.desired_reach} onChange={(e) => update("desired_reach", e.target.value)} />
          </div>
          <div>
            <label className="label">Total budget (₹)</label>
            <input className="input" type="number" required min={1} value={form.total_budget} onChange={(e) => update("total_budget", e.target.value)} />
          </div>
        </div>

        <div>
          <label className="label">Notes</label>
          <textarea className="input" rows={3} value={form.notes} onChange={(e) => update("notes", e.target.value)} />
        </div>

        <button type="submit" className="btn-primary w-full" disabled={submitting}>
          {submitting ? "Creating…" : "Create Brief & Find Creators"}
        </button>
      </form>
    </div>
  );
}
