🐾 ChatCat Assistant
<div align="center">
University of Arizona Software Engineering Chatbot
A full-stack AI chatbot providing information about the University of Arizona's Software Engineering programs
Show Image
Show Image
Show Image
Show Image
</div>

📋 Table of Contents

Features
Architecture
Prerequisites
Installation

1. Install Required Programs
2. Backend Setup
3. Frontend Setup


Running the Application
Project Structure
Troubleshooting
Deployment
Credits


✨ Features

🧠 AI-Powered Responses using Ollama's local LLM
💬 Real-time Chat Interface built with React
🔍 Semantic Search with embedding-based retrieval
⚡ Fast API Backend with Python FastAPI
🎨 Modern UI powered by Vite
🔒 Privacy-First - all processing happens locally


🏗️ Architecture
┌─────────────────┐
│  React Frontend │ → http://localhost:5173
│   (Vite Dev)    │
└────────┬────────┘
         │ proxy
         ↓
┌─────────────────┐
│ FastAPI Backend │ → http://127.0.0.1:8000
│   (Python 3.x)  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Ollama API    │ → http://localhost:11434
│  (Local Models) │
└─────────────────┘

📦 Prerequisites
Before you begin, ensure you have the following installed:
ToolVersionDownload LinkPython3.10+python.orgNode.js18+ (LTS)nodejs.orgOllamaLatestollama.com

💡 Windows Users: Run all commands in Command Prompt (cmd) with Administrator privileges when possible.


🚀 Installation
1. Install Required Programs
🐍 Python
Check if Python is installed:
cmdpython --version
✅ During installation, make sure to check "Add Python to PATH"
📦 Node.js & npm
Check if Node.js is installed:
cmdnode -v
npm -v
🧠 Ollama
After installing Ollama, verify it's running:
cmdollama --version
Pull the required models:
cmdollama pull nomic-embed-text
ollama pull gemma3:1b

2. Backend Setup (FastAPI + Ollama)
Navigate to Project Root
cmdcd F:\SFWE403-Group-6-Project

📁 Adjust the path to match your project location

Create Virtual Environment
cmdpython -m venv .venv
Activate Virtual Environment
cmd.venv\Scripts\activate
You should see (.venv) prefix in your terminal
Install Dependencies
cmdpip install -r requirements.txt
This installs:

fastapi - Web framework
uvicorn - ASGI server
pydantic - Data validation
numpy - Numerical operations
tiktoken - Token counting
ollama - LLM interface


3. Frontend Setup (React + Vite)
Open New Terminal

⚠️ Keep the backend terminal running

Navigate to Frontend Directory
cmdcd F:\SFWE403-Group-6-Project\ChatCat-Assistant
Install Dependencies
cmdnpm install
This installs:

React & React DOM
Vite build tool
Babel compiler
UI dependencies


▶️ Running the Application
Terminal 1: Start Backend
cmdcd F:\SFWE403-Group-6-Project
.venv\Scripts\activate
python main.py
✅ Backend running at: http://127.0.0.1:8000
Terminal 2: Start Frontend
cmdcd F:\SFWE403-Group-6-Project\ChatCat-Assistant
npm run dev
```
✅ Frontend running at: `http://localhost:5173`

### 🎉 Access the Application
Open your browser and navigate to: **http://localhost:5173**

---

## 📂 Project Structure
```
SFWE403-Group-6-Project/
│
├── 📄 main.py                    # FastAPI backend server
├── 📄 requirements.txt           # Python dependencies
├── 📄 README.md                  # This file
├── 📄 ChatBot.md                 # Knowledge base
├── 📁 .venv/                     # Python virtual environment
│
└── 📁 ChatCat-Assistant/         # React frontend
    ├── 📄 package.json           # Node dependencies
    ├── 📄 vite.config.js         # Vite configuration
    ├── 📁 src/
    │   ├── 📄 App.jsx            # Main React component
    │   ├── 📄 App.css            # Styles
    │   └── 📁 assets/            # Static assets
    └── 📁 node_modules/          # Installed packages

🚑 Troubleshooting
<details>
<summary><b>ModuleNotFoundError</b></summary>
Ensure virtual environment is activated and dependencies are installed:
cmd.venv\Scripts\activate
pip install -r requirements.txt
</details>
<details>
<summary><b>Ollama not found</b></summary>

Verify Ollama is installed: ollama --version
Ensure Ollama service is running in the background
Try restarting Ollama from the system tray

</details>
<details>
<summary><b>vite: command not found</b></summary>
Reinstall frontend dependencies:
cmdcd ChatCat-Assistant
npm install
</details>
<details>
<summary><b>CORS or API not connecting</b></summary>

Verify backend is running on port 8000
Check vite.config.js proxy target matches backend URL
Ensure no firewall is blocking local connections

</details>
<details>
<summary><b>Port already in use</b></summary>

Close other running servers
Change port in main.py (backend) or vite.config.js (frontend)
Kill process using the port: netstat -ano | findstr :8000

</details>

🧾 Quick Reference
TaskCommandActivate Python environment.venv\Scripts\activateInstall backend dependenciespip install -r requirements.txtRun backendpython main.pyNavigate to frontendcd ChatCat-AssistantInstall frontend dependenciesnpm installRun frontendnpm run devView applicationOpen http://localhost:5173

🌐 Deployment
<details>
<summary><b>Backend Deployment Options</b></summary>
Deploy to cloud platforms:

Render
Railway
Fly.io

Required environment variables:
envEMBED_MODEL=nomic-embed-text
LLM=gemma3:1b
</details>
<details>
<summary><b>Frontend Deployment Options</b></summary>
Deploy to static hosting:

Netlify
Vercel

Build command:
cmdnpm run build
Deploy the generated dist/ folder
</details>

👥 Credits
<div align="center">
SFWE403 Group 6 – ChatCat Assistant
University of Arizona
Built with ❤️ using FastAPI • Ollama • React • Vite

Technologies Used
Show Image
Show Image
Show Image
Show Image
Show Image
Show Image
</div>

<div align="center">
⬆ Back to Top
</div>