# 🎙️ Audio Podcast Generator

An end-to-end AI-powered automated podcast generation system. This project transforms topics, articles, and research queries into natural, multi-speaker conversational podcasts using Large Language Models (LLMs) and Neural Text-to-Speech (TTS) voice cloning engines.

---

## 🌟 Key Features

- **Multi-Speaker Conversational Script Generation**:
  - Leverages local LLMs via **Ollama** (e.g., `llama3.2`, `mistral`) or cloud LLMs via **Google Gemini API** (`gemini-3.1-flash-lite`).
  - Automatically formats dialogues between distinct hosts with natural banter, questions, and transitions.

- **Neural Voice Synthesis & Cloning**:
  - **XTTS-v2** local neural voice cloning for zero-shot speaker adaptation from short audio samples.
  - **Fish Audio** cloud TTS integration for ultra-realistic voice quality.
  - Custom voice cloning upload: Provide reference voice samples to create unique speaker identities.

- **Audio Post-Processing Pipeline**:
  - Automated stitching and cross-fading of multi-speaker dialogue turns using **FFmpeg**.
  - Background music blending and ducking for professional podcast production.
  - Exports standard high-fidelity audio formats (WAV/MP3).

- **Modern Web Interface**:
  - React + TypeScript + Vite frontend with a clean, responsive audio workstation interface.
  - Live progress tracking, script preview, audio playback, and sample management.

---

## 🏗️ Architecture

---

## 🚀 Getting Started

### Prerequisites

1. **Python 3.10+** (Recommended: Python 3.11)
2. **Node.js 18+** & `npm`
3. **FFmpeg**: Ensure FFmpeg is installed and accessible in your system `PATH`.
4. *(Optional)* **Ollama**: For local offline script generation. Install from [ollama.com](https://ollama.com).

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd podcast-backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env     # Windows
# or: cp .env.example .env # Linux/macOS
```

Edit `.env` to configure your keys (optional depending on selected engine):
```ini
GEMINI_API_KEY="your_gemini_api_key"
GEMINI_MODEL=gemini-3.1-flash-lite
FISH_AUDIO_API_KEY="your_fish_audio_api_key"
AUDIO_OUTPUT_DIR=audio_output
```

Run the backend server:
```bash
uvicorn app.main:app --reload --port 8000
```
Backend API will be available at: `http://localhost:8000` (API Docs at `http://localhost:8000/docs`).

---

### 2. Frontend Setup

In a new terminal:

```bash
# Navigate to frontend directory
cd podcast-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
Frontend UI will be running at: `http://localhost:5173` (or the port indicated in the terminal).

---

## 🧪 Testing

Run backend tests using pytest:

```bash
cd podcast-backend
pytest tests/
```

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).