import { useRef, useState } from "react";
import { sendChat } from "../api";
import type { ChatMessage } from "../types";

interface Props {
  enabled: boolean;
}

function _userMsg(content: string): ChatMessage {
  return { role: "user", content };
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const cls = msg.role === "user" ? "msg msg-user" : "msg msg-assistant";
  return <div className={cls}>{msg.content}</div>;
}

export function Chat({ enabled }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const submit = async () => {
    const text = input.trim();
    if (!text || loading) return;
    const next: ChatMessage[] = [...messages, _userMsg(text)];
    setMessages(next);
    setInput("");
    setLoading(true);
    setError("");
    const reply = await sendChat(next).catch((e: Error) => { setError(e.message); return ""; });
    if (reply) setMessages([...next, { role: "assistant", content: reply }]);
    setLoading(false);
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
  };

  if (!enabled) {
    return (
      <div className="chat-disabled">
        <p>🤖 LLM not configured.</p>
        <p>Set <code>OPENAI_API_KEY</code> (and optionally <code>OPENAI_BASE_URL</code>, <code>OPENAI_MODEL</code>) to enable AI chat.</p>
        <p>Works with OpenAI, Ollama, Groq, and any OpenAI-compatible endpoint.</p>
      </div>
    );
  }

  return (
    <div className="chat-wrap">
      <div className="chat-history">
        {messages.length === 0 && <p className="chat-hint">Ask anything about your vault…</p>}
        {messages.map((m, i) => <MessageBubble key={i} msg={m} />)}
        {loading && <div className="msg msg-assistant chat-thinking">Thinking…</div>}
        {error && <div className="chat-error">{error}</div>}
        <div ref={bottomRef} />
      </div>
      <div className="chat-input-row">
        <input
          className="chat-input"
          type="text"
          placeholder="Ask about your notes…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          disabled={loading}
        />
        <button className="chat-send" onClick={submit} disabled={loading || !input.trim()}>
          ↑
        </button>
      </div>
    </div>
  );
}
