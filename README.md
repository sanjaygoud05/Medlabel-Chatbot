# 💊 MedLabel AI — Medicine Label Interpreter & Patient Reminder Assistant

MedLabel AI is an intelligent healthcare assistant powered by **Gemini 3.8 Flash**. Patients and caregivers can upload photos of medicine strips, blister packs, and prescriptions to receive plain-English explanations of dosage, active ingredients, precautions, and **real-time expiry verification**. Users can also generate and email themselves a personalized daily reminder schedule.

---

## ✨ Key Features

- **📸 Multimodal Label Recognition**: Upload clear photos of medicine strips, blister packs, bottles, or prescriptions.
- **📅 Deterministic Live Expiry Verification**: Compares the label's printed expiry date against today's live calendar date and alerts if medication is expired or expiring soon.
- **💬 Plain-Language Explanations**: Converts complex pharmaceutical jargon into simple, patient-friendly guidance.
- **📧 One-Click Email Reminder Plan**: Generates and emails a personalized, pixel-perfect HTML daily schedule directly to the patient's inbox.
- **🌓 Dark & Light Mode**: Clean, accessible UI designed for patients of all ages.

---

## 🛠️ Tech Stack

- **Framework**: Python, Streamlit
- **AI Model**: Google Gemini 3.8 Flash (`google-genai` SDK)
- **Email Service**: Python `smtplib` (SSL encrypted HTML email)

---

## 🚀 Quickstart & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sanjaygoud05/Medlabel-Chatbot.git
   cd Medlabel-Chatbot
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Secrets:**
   Create `.streamlit/secrets.toml`:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key"
   GMAIL_ADDRESS = "your-gmail@gmail.com"
   GMAIL_APP_PASSWORD = "your-gmail-app-password"
   ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

---

## ⚠️ Medical Disclaimer

*MedLabel AI is designed solely for informational and educational purposes to help users read printed packaging text. It is not a substitute for professional medical advice, diagnosis, or treatment. Always follow your doctor's or pharmacist's direct instructions.*
