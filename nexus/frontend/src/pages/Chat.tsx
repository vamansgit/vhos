import { useEffect, useRef, useState } from "react";
import { api } from "@/api/client";
import type { ChatMessageOut, ChatSendResponse } from "@/api/types";
import { useVoice } from "@/lib/useVoice";
import { FinanceWidget, OnboardWidget, SellWidget, SourceMatchWidget } from "@/widgets/ChatWidgets";

const SUGGESTIONS = [
  "Find me suppliers for 500 units of copper water bottles under ₹250 each",
  "Build me a store, ship pan-India, minimal and earthy style",
  "How much did I make this month, what's my margin?",
  "Update my brand's target market to include the US",
];

function Widget({ message }: { message: ChatMessageOut }) {
  const payload = message.structured_payload ?? {};
  if (message.module === "source" && payload.sourcing_request_id) {
    return <SourceMatchWidget sourcingRequestId={String(payload.sourcing_request_id)} />;
  }
  if (message.module === "finance" && "revenue" in payload) {
    return <FinanceWidget payload={payload} />;
  }
  if (message.module === "sell" && payload.store_id) {
    return <SellWidget storeId={String(payload.store_id)} />;
  }
  if (message.module === "onboard") {
    return <OnboardWidget payload={payload} />;
  }
  return null;
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessageOut[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const voice = useVoice();

  useEffect(() => {
    api
      .get<ChatMessageOut[]>("/chat/history")
      .then(setMessages)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendText(text: string) {
    if (!text.trim() || sending) return;
    setSending(true);
    setInput("");

    const optimisticUser: ChatMessageOut = {
      id: `local-${Date.now()}`,
      role: "user",
      module: "none",
      content: text,
      structured_payload: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUser]);

    try {
      const response = await api.post<ChatSendResponse>("/chat", { text });
      const assistantMessage: ChatMessageOut = {
        id: `local-reply-${Date.now()}`,
        role: "assistant",
        module: response.module,
        content: response.reply,
        structured_payload: response.payload,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      if (voice.supported) voice.speak(response.reply);
    } finally {
      setSending(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    sendText(input);
  }

  function handleMic() {
    if (voice.isListening) {
      voice.stopListening();
      return;
    }
    voice.startListening((transcript) => sendText(transcript));
  }

  return (
    <div className="mx-auto flex h-screen max-w-3xl flex-col px-4">
      <div className="flex-1 overflow-y-auto py-6">
        {loading ? (
          <div className="text-ink-500">Loading…</div>
        ) : messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <h1 className="text-xl font-semibold text-ink-900">What do you want to get done today?</h1>
            <p className="mt-1 max-w-md text-sm text-ink-500">
              Describe what you need in plain language — sourcing, your storefront, or your numbers.
            </p>
            <div className="mt-6 grid max-w-lg gap-2">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => sendText(s)} className="btn-secondary text-left text-sm">
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((m) => (
              <div key={m.id} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                    m.role === "user" ? "bg-brand-600 text-white" : "border border-ink-200 bg-white text-ink-900"
                  }`}
                >
                  <div>{m.content}</div>
                  {m.role === "assistant" && <Widget message={m} />}
                </div>
              </div>
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="sticky bottom-0 flex items-center gap-2 border-t border-ink-200 bg-ink-50 py-4">
        <input
          className="input flex-1"
          placeholder="Describe what you need, or tap the mic…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={sending}
        />
        {voice.supported && (
          <button
            type="button"
            onClick={handleMic}
            className={`btn ${voice.isListening ? "bg-red-100 text-red-700" : "btn-secondary"}`}
            title="Voice input"
          >
            {voice.isListening ? "● Listening…" : "🎙"}
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={sending || !input.trim()}>
          {sending ? "…" : "Send"}
        </button>
      </form>
    </div>
  );
}
