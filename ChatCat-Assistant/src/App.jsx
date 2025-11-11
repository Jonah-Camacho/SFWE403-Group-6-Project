import { useState } from "react";
import "./App.css";
import azLogo from "./assets/UAENGR_logo.png";
import gearIcon from "./assets/gear-icon.svg";

function App() {
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text:
        "Hello! My name is ChatCat. I am your personal guide to Software Engineering at the University of Arizona. What can I help you with today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);

  const MAX_CHARS = 200;

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    if (input.length > MAX_CHARS) {
      setError(true);
      return;
    }

    const userMsg = { sender: "user", text: input.trim() };
    const nextHistory = [...messages, userMsg];

    setMessages(nextHistory);
    setInput("");
    setError(false);
    setLoading(true);

    try {
      // Build history in backend format
      const historyForApi = nextHistory.map(({ sender, text }) => ({
        role: sender === "user" ? "user" : "assistant",
        content: text,
      }));

      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg.text,
          history: historyForApi,
          new_session: false,
          k_ctx: 5,
        }),
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || `HTTP ${res.status}`);
      }

      const data = await res.json(); // { reply: string }
      setMessages([...nextHistory, { sender: "bot", text: data.reply }]);
    } catch (e) {
      setMessages([
        ...nextHistory,
        { sender: "bot", text: "Error contacting server: " + e.message },
      ]);
    } finally {
      setLoading(false);
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
        </div>

        {/* User Input Area */}
        <div className="input-area">
          <input
            type="text"
            placeholder={
              loading
                ? "Waiting for ChatCat to respond..."
                : "Type your message..."
            }
            value={input}
            onChange={handleInputChange}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            disabled={loading}
          />
          <button onClick={handleSend} disabled={loading}>
            Send
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

export default App;
