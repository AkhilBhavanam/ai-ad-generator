#  AI Video Generator

Generate professional video ads from product URLs using AI-powered scraping, script generation, and video creation.

---

## 🛠️ Backend (FastAPI, MoviePy, ElevenLabs, OpenAI)

### Prerequisites

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (required for MoviePy)
- (Optional) [Playwright browsers](https://playwright.dev/python/docs/browsers) for advanced scraping

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd 
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env` and fill in your API keys:
     ```
     OPENAI_API_KEY=your-openai-key
     ELEVENLABS_API_KEY=your-elevenlabs-key
     HOST=0.0.0.0
     PORT=8000
     DEBUG=True
     ```
   - (You may need to create `.env.example` if it's missing.)

5. **Install Playwright browsers (for scraping):**
   ```bash
   playwright install
   ```

### Running the Backend

```bash
python main.py
```

- The API will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🖥️ Frontend (React + Vite + Tailwind)

### Prerequisites

- Node.js 18+
- npm

### Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

- The frontend will be available at: [http://localhost:3000](http://localhost:3000)

---

## 🔗 Connecting Frontend and Backend

- The frontend is pre-configured to call the backend at `http://localhost:8000/api`.
- Make sure both servers are running for full functionality.

---

## 🧩 Features

- Scrape product data from e-commerce URLs (Amazon, eBay, Shopify, Etsy, etc.)
- Generate ad scripts using OpenAI
- Create videos with AI voiceover (ElevenLabs/gTTS), karaoke subtitles, and background music
- Download and share generated videos

---

## 📝 Troubleshooting

- **No audio in video?**  
  Ensure ffmpeg is installed and the backend logs show successful audio generation.
- **Scraping issues?**  
  Make sure Playwright browsers are installed and up to date.
- **API key errors?**  
  Double-check your `.env` file for valid OpenAI and ElevenLabs keys.

--- 