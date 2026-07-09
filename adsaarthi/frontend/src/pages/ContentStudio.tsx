import { useEffect, useState } from "react";
import { api, ApiError } from "@/api/client";
import type { ContentDraft, ContentDraftStatus } from "@/api/types";
import { formatDate, titleCase } from "@/lib/format";

type Tab = "blog" | "ad_copy" | "image" | "calendar";

const STATUS_STYLES: Record<ContentDraftStatus, string> = {
  draft: "bg-ink-100 text-ink-700",
  approved: "bg-brand-100 text-brand-800",
  published: "bg-blue-100 text-blue-800",
  rejected: "bg-red-100 text-red-700",
};

export default function ContentStudio() {
  const [tab, setTab] = useState<Tab>("blog");
  const [drafts, setDrafts] = useState<ContentDraft[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [blogForm, setBlogForm] = useState({ topic: "", keywords: "" });
  const [adForm, setAdForm] = useState({ product_or_offer: "", platforms: ["instagram", "youtube", "google_search"] });
  const [imageForm, setImageForm] = useState({ prompt: "", format: "instagram_post" });

  async function loadDrafts() {
    setLoading(true);
    const data = await api.get<ContentDraft[]>("/content");
    setDrafts(data);
    setLoading(false);
  }

  useEffect(() => {
    loadDrafts();
  }, []);

  async function generateBlog(e: React.FormEvent) {
    e.preventDefault();
    setGenerating(true);
    setError(null);
    try {
      await api.post("/content/blog", {
        topic: blogForm.topic,
        keywords: blogForm.keywords.split(",").map((k) => k.trim()).filter(Boolean),
      });
      setBlogForm({ topic: "", keywords: "" });
      await loadDrafts();
      setTab("calendar");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  async function generateAdCopy(e: React.FormEvent) {
    e.preventDefault();
    setGenerating(true);
    setError(null);
    try {
      await api.post("/content/ad-copy", adForm);
      setAdForm({ ...adForm, product_or_offer: "" });
      await loadDrafts();
      setTab("calendar");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  async function generateImage(e: React.FormEvent) {
    e.preventDefault();
    setGenerating(true);
    setError(null);
    try {
      await api.post("/content/image", imageForm);
      setImageForm({ ...imageForm, prompt: "" });
      await loadDrafts();
      setTab("calendar");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  async function updateStatus(id: string, status: ContentDraftStatus) {
    const updated = await api.patch<ContentDraft>(`/content/${id}`, { status });
    setDrafts((prev) => prev.map((d) => (d.id === id ? updated : d)));
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-ink-900">AI Content Studio</h1>
        <p className="text-sm text-ink-500">
          Generate blogs, ad copy, and visual concepts on-brand — every draft needs your review before publishing.
        </p>
      </div>

      <div className="flex gap-2 border-b border-ink-200">
        {(["blog", "ad_copy", "image", "calendar"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium ${
              tab === t ? "border-b-2 border-brand-600 text-brand-700" : "text-ink-500 hover:text-ink-800"
            }`}
          >
            {t === "calendar" ? `Content Calendar (${drafts.length})` : t === "ad_copy" ? "Ad Copy" : titleCase(t)}
          </button>
        ))}
      </div>

      {error && <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

      {tab === "blog" && (
        <form onSubmit={generateBlog} className="card max-w-xl space-y-4">
          <div>
            <label className="label">Topic</label>
            <input className="input" required value={blogForm.topic} onChange={(e) => setBlogForm({ ...blogForm, topic: e.target.value })} placeholder="Benefits of Vitamin C serum for Indian skin" />
          </div>
          <div>
            <label className="label">SEO keywords (comma-separated)</label>
            <input className="input" value={blogForm.keywords} onChange={(e) => setBlogForm({ ...blogForm, keywords: e.target.value })} placeholder="vitamin c serum, skincare routine" />
          </div>
          <button type="submit" className="btn-primary" disabled={generating}>
            {generating ? "Generating…" : "Generate Blog Draft"}
          </button>
        </form>
      )}

      {tab === "ad_copy" && (
        <form onSubmit={generateAdCopy} className="card max-w-xl space-y-4">
          <div>
            <label className="label">Product or offer</label>
            <input className="input" required value={adForm.product_or_offer} onChange={(e) => setAdForm({ ...adForm, product_or_offer: e.target.value })} placeholder="Vitamin C Glow Serum — 20% off launch week" />
          </div>
          <div>
            <label className="label">Platforms</label>
            <div className="flex gap-4 text-sm">
              {["instagram", "youtube", "google_search"].map((p) => (
                <label key={p} className="flex items-center gap-1.5">
                  <input
                    type="checkbox"
                    checked={adForm.platforms.includes(p)}
                    onChange={(e) =>
                      setAdForm((prev) => ({
                        ...prev,
                        platforms: e.target.checked ? [...prev.platforms, p] : prev.platforms.filter((x) => x !== p),
                      }))
                    }
                  />
                  {titleCase(p)}
                </label>
              ))}
            </div>
          </div>
          <button type="submit" className="btn-primary" disabled={generating || adForm.platforms.length === 0}>
            {generating ? "Generating…" : "Generate Ad Copy"}
          </button>
        </form>
      )}

      {tab === "image" && (
        <form onSubmit={generateImage} className="card max-w-xl space-y-4">
          <div>
            <label className="label">Visual concept prompt</label>
            <textarea className="input" rows={3} required value={imageForm.prompt} onChange={(e) => setImageForm({ ...imageForm, prompt: e.target.value })} placeholder="Serum bottle on marble surface with soft morning light" />
          </div>
          <div>
            <label className="label">Format</label>
            <select className="input" value={imageForm.format} onChange={(e) => setImageForm({ ...imageForm, format: e.target.value })}>
              <option value="instagram_post">Instagram Post</option>
              <option value="banner">Banner</option>
              <option value="story">Story</option>
            </select>
          </div>
          <p className="text-xs text-ink-500">
            MVP produces a structured visual-direction brief (composition, colors, copy overlay) rather than a
            rendered image — swap in an image generation API to render the final asset from this spec.
          </p>
          <button type="submit" className="btn-primary" disabled={generating}>
            {generating ? "Generating…" : "Generate Visual Concept"}
          </button>
        </form>
      )}

      {tab === "calendar" && (
        <div className="space-y-3">
          {loading ? (
            <div className="text-ink-500">Loading…</div>
          ) : drafts.length === 0 ? (
            <div className="card text-center text-sm text-ink-500">No content generated yet.</div>
          ) : (
            drafts.map((d) => (
              <details key={d.id} className="card">
                <summary className="flex cursor-pointer items-center justify-between">
                  <div>
                    <span className="badge mr-2 bg-ink-100 text-ink-600">{titleCase(d.type)}</span>
                    <span className="font-medium text-ink-900">{d.title}</span>
                  </div>
                  <span className={`badge ${STATUS_STYLES[d.status]}`}>{titleCase(d.status)}</span>
                </summary>
                <pre className="mt-3 whitespace-pre-wrap font-sans text-sm text-ink-700">{d.body}</pre>
                <div className="mt-3 flex items-center justify-between border-t border-ink-100 pt-3 text-xs text-ink-500">
                  <span>
                    Generated {formatDate(d.created_at)} via {d.generated_by}
                    {d.platform_variant ? ` · ${titleCase(d.platform_variant)}` : ""}
                  </span>
                  <div className="flex gap-2">
                    {d.status === "draft" && (
                      <button className="btn-secondary" onClick={() => updateStatus(d.id, "approved")}>
                        Approve
                      </button>
                    )}
                    {d.status === "approved" && (
                      <button className="btn-primary" onClick={() => updateStatus(d.id, "published")}>
                        Mark Published
                      </button>
                    )}
                  </div>
                </div>
              </details>
            ))
          )}
        </div>
      )}
    </div>
  );
}
