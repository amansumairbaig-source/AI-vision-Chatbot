# 🥗 MacroSnap - AI Vision Nutrition Chatbot

MacroSnap is an AI-powered nutrition assistant built with **Streamlit**, **Google Gemini**, and **Twilio WhatsApp API**. It allows users to log meals by taking photos or typing descriptions, automatically estimating calories and macros (protein, carbs, fat), and sending a daily meal summary straight to WhatsApp.

---

## ✨ Features

- **📸 Multimodal Food Recognition**: Snap a photo or describe what you ate. Powered by Google Gemini (`gemini-3.7-flash` / `gemini-3.6-flash`).
- **🥗 Instant Macro & Calorie Breakdown**: Estimates calories, protein, carbohydrates, and fats in real-time.
- **📲 WhatsApp Daily Summary**: Consolidates daily meals into a single text report sent via Twilio's WhatsApp Content API.
- **⚡ Fast & Interactive Web UI**: Built with Streamlit for a clean, responsive experience.

---

## 🛠️ Tech Stack

- **Frontend & App Logic**: [Streamlit](https://streamlit.io/)
- **AI & Vision Model**: [Google GenAI SDK (`google-genai`)](https://ai.google.dev/)
- **Messaging**: [Twilio Python SDK](https://www.twilio.com/)

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-vision-chatbot.git
cd ai-vision-chatbot
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# On macOS/Linux:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Secrets
Create a file at `.streamlit/secrets.toml` by copying `.streamlit/secrets.toml.example`:

```toml
GEMINI_API_KEY = "your-gemini-api-key"
TWILIO_ACCOUNT_SID = "your-twilio-account-sid"
TWILIO_AUTH_TOKEN = "your-twilio-auth-token"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
TWILIO_CONTENT_SID = "your-twilio-content-sid"
```

> **Note**: Never commit `.streamlit/secrets.toml` to git. It is included in `.gitignore`.

### 5. Run the Application
```bash
streamlit run app.py
```

---

## 🚢 Deploying to Streamlit Community Cloud

1. Push this repository to **GitHub**.
2. Visit [share.streamlit.io](https://share.streamlit.io) and connect your GitHub account.
3. Select your repository and set the main file path to `app.py`.
4. In **Advanced Settings > Secrets**, paste the contents of your `.streamlit/secrets.toml`.
5. Click **Deploy**!
