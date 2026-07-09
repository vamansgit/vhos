interface StatCardProps {
  label: string;
  value: string;
  hint?: string;
  tone?: "default" | "positive" | "negative";
}

const TONE_CLASSES: Record<NonNullable<StatCardProps["tone"]>, string> = {
  default: "text-ink-900",
  positive: "text-brand-700",
  negative: "text-red-600",
};

export default function StatCard({ label, value, hint, tone = "default" }: StatCardProps) {
  return (
    <div className="card">
      <div className="text-xs font-medium uppercase tracking-wide text-ink-500">{label}</div>
      <div className={`mt-2 text-2xl font-semibold ${TONE_CLASSES[tone]}`}>{value}</div>
      {hint && <div className="mt-1 text-xs text-ink-500">{hint}</div>}
    </div>
  );
}
