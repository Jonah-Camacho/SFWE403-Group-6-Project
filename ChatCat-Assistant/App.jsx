import { useState } from "react";
import "./App.css";
import azLogo from "./assets/UAENGR_logo.png";
import gearIcon from "./assets/gear-icon.svg";

// Convert your UI messages to the backend "history" schema
const toHistory = (msgs) =>
  msgs.map((m) => ({
    role: m.sender === "user" ? "user" : "assistant",
    content: m.text,
  }));

export default function App() {
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text:
        "Hello! My name is ChatCat. I am your personal guide to Software Engineering at the University of Arizona. What can I help you with today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  const MAX_CHARS = 200;

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || busy) return;

    if (trimmed.length > MAX_CHARS) {
      setError(true);
      return;
    }

    // push user message into UI immediately
    const userMsg = { sender: "user", text: trimmed };
    const nextMsgs = [...messages, userMsg];
    setMessages(nextMsgs);
    setInput("");
    setError(false);
    setBusy(true);

    try {
      // Build full history for the backend
      const history = toHistory(nextMsgs);
      const userTurns = history.filter((h) => h.role === "user").length;
      const isNew = userTurns === 1; // treat first user message as a new session

      // Call FastAPI through Vite proxy -> /api/chat -> http://localhost:8000/chat
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          history,
          new_session: isNew,
          k_ctx: 5,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Backend ${res.status}: ${text}`);
      }

      const data = await res.json(); // { reply: string }

      // show assistant reply
      setMessages((prev) => [...prev, { sender: "bot", text: data.reply }]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: `Error talking to server: ${e.message}`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    if (value.length > MAX_CHARS) {
      setError(true);
      setInput(value.slice(0, MAX_CHARS));
    } else {
      setError(false);
      setInput(value);
    }
  };

  return (
    <div className="app">
      {/* Header/Nav-Bar */}
      <header className="header">
        <div className="header-left">
          <img src={azLogo} className="logo az" alt="AZ logo" />
        </div>
        <div className="header-center">
          <h1>ChatCat Assistant</h1>
        </div>
        <div className="header-right">
          <img src={gearIcon} className="logo-settings" alt="settings-logo" />
        </div>
      </header>

      {/* Chat Container */}
      <div className="chat-container">
        <div className="chat-box">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              <div className="bubble">{msg.text}</div>
            </div>
          ))}
          {busy && (
            <div className="message bot">
              <div className="bubble">Thinking…</div>
            </div>
          )}
        </div>

        {/* User Input Area */}
        <div className="input-area">
          <input
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={handleInputChange}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={busy}
          />
          <button onClick={handleSend} disabled={busy}>
            {busy ? "Sending…" : "Send"}
          </button>
        </div>

        {/* Character Counter */}
        <div className={`char-Counter ${error ? "error" : ""}`}>
          {input.length} / {MAX_CHARS}
        </div>

        {/* Error Messaging */}
        {error && (
          <div className="error-message">
            Character limit exceeded (max {MAX_CHARS})
          </div>
        )}
      </div>
    </div>
  );
}