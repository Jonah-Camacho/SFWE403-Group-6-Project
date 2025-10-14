import { useState } from "react";
import "./App.css";
import azLogo from "./assets/UAENGR_logo.png";

function App() {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hello! My name is ChatCat. I am your personal guide to Software Engineering at the University of Arizona. What can I help you with today?"},
  ]);
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim()) return;

    // Add user message
    const newMessages = [...messages, { sender: "user", text: input }];
    setMessages(newMessages);
    setInput("");

    // Simulate bot response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "This is a placeholder response. (Later replaced with API.)" },
      ]);
    }, 600);
  };

  return (
    <div className="app">
      <header className="header">
        <h2>      </h2>
        <img src={azLogo} className="logo az" alt="AZ logo" />
        <h2> Software Engineering ChatCat Assistant</h2>
      </header>
      <header2 className="header2">
      </header2>

      <div className="chat-container">
        <div className="chat-box">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              <div className="bubble">{msg.text}</div>
            </div>
          ))}
        </div>

        <div className="input-area">
          <input
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
          <button onClick={handleSend}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;
