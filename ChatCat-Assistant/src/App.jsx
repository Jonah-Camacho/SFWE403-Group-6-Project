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
<>
    <header className="header">
      <div className="header-left">
        <img src={azLogo} className="logo az" alt="AZ logo" />
      </div>

      <div className="header-center">
        <h1>ChatCat Assistant</h1>
      </div>
    </header>

    <div className="app">
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
</>
  );
}

export default App;
