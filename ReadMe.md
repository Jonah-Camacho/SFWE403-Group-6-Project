# 🐾 ChatCat Assistant

### *University of Arizona Software Engineering Chatbot*

A full-stack AI chatbot providing information about the **University of Arizona's Software Engineering programs**.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Running the Application](#-running-the-application)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Deployment](#-deployment)
- [Credits](#-credits)

---

## ✨ Features

- 🧠 **AI-Powered Responses** using Ollama's local LLM
- 💬 **Real-time Chat Interface** built with React
- 🔍 **Semantic Search** with embedding-based retrieval
- ⚡ **Fast API Backend** with Python FastAPI
- 🎨 **Modern UI** powered by Vite
- 🔒 **Privacy-First** - all processing happens locally

---

## 🏗️ Architecture

```
React Frontend (Vite) → http://localhost:5173
         ↓ (proxy)
FastAPI Backend       → http://127.0.0.1:8000
         ↓
Ollama API            → http://localhost:11434
```

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python** 3.10+ - [Download](https://www.python.org/downloads/)
- **Node.js** 18+ (LTS) - [Download](https://nodejs.org/)
- **Ollama** Latest - [Download](https://ollama.com/download)

> 💡 **Windows Users**: Run all commands in **Command Prompt (cmd)** with Administrator privileges when possible.

---

## 🚀 Installation

### 1. Install Required Programs

#### Python

Check if Python is installed:
```cmd
python --version
```

✅ During installation, make sure to check **"Add Python to PATH"**

#### Node.js & npm

Check if Node.js is installed:
```cmd
node -v
npm -v
```

#### Ollama

After installing Ollama, verify it's running:
```cmd
ollama --version
```

Pull the required models:
```cmd
ollama pull nomic-embed-text
ollama pull gemma3:1b
```

---

### 2. Backend Setup

Navigate to project root:
```cmd
cd F:\SFWE403-Group-6-Project
```

Create virtual environment:
```cmd
python -m venv .venv
```

Activate virtual environment:
```cmd
.venv\Scripts\activate
```

Install dependencies:
```cmd
pip install -r requirements.txt
```

---

### 3. Frontend Setup

Open new terminal and navigate to frontend:
```cmd
cd F:\SFWE403-Group-6-Project\ChatCat-Assistant
```

Install dependencies:
```cmd
npm install
```

---

## ▶️ Running the Application

### Terminal 1: Start Backend
```cmd
cd F:\SFWE403-Group-6-Project
.venv\Scripts\activate
python main.py
```

### Terminal 2: Start Frontend
```cmd
cd F:\SFWE403-Group-6-Project\ChatCat-Assistant
npm run dev
```

### Access the Application
Open your browser: **http://localhost:5173**

---

## 📂 Project Structure

```
SFWE403-Group-6-Project/
│
├── main.py                    # FastAPI backend server
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── ChatBot.md                 # Knowledge base
├── .venv/                     # Python virtual environment
│
└── ChatCat-Assistant/         # React frontend
    ├── package.json
    ├── vite.config.js
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   └── assets/
    └── node_modules/
```

---

## 🚑 Troubleshooting

**ModuleNotFoundError**
```cmd
.venv\Scripts\activate
pip install -r requirements.txt
```

**Ollama not found**
- Verify installation: `ollama --version`
- Ensure Ollama service is running
- Try restarting from system tray

**vite: command not found**
```cmd
cd ChatCat-Assistant
npm install
```

**CORS or API not connecting**
- Verify backend runs on port 8000
- Check `vite.config.js` proxy target
- Ensure no firewall blocks local connections

**Port already in use**
- Close other servers
- Change port in `main.py` or `vite.config.js`

---

## 🧾 Quick Reference

| Task | Command |
|------|---------|
| Activate Python environment | `.venv\Scripts\activate` |
| Install backend dependencies | `pip install -r requirements.txt` |
| Run backend | `python main.py` |
| Navigate to frontend | `cd ChatCat-Assistant` |
| Install frontend dependencies | `npm install` |
| Run frontend | `npm run dev` |
| View application | `http://localhost:5173` |

---

## 🌐 Deployment

### Backend Options
- [Render](https://render.com/)
- [Railway](https://railway.app/)
- [Fly.io](https://fly.io/)

Required environment variables:
```env
EMBED_MODEL=nomic-embed-text
LLM=gemma3:1b
```

### Frontend Options
- [Netlify](https://www.netlify.com/)
- [Vercel](https://vercel.com/)

Build command:
```cmd
npm run build
```
