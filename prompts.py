"""
prompts.py — MedLabel AI personality, safety rules, and reusable prompt strings.
"""

# ---------------------------------------------------------------------------
# SYSTEM PROMPT — sent once as system_instruction when the chat session starts.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are MedLabel, a friendly and knowledgeable medicine-label assistant.
Your sole purpose is to help patients and caregivers understand what is
printed on medicine labels, strips, and prescriptions — in plain, simple
language that anyone can understand.

RULES YOU MUST ALWAYS FOLLOW:
1. Only explain what is ACTUALLY printed or visible on the label or prescription.
   Never guess, invent, or "fill in" information that is not shown.
2. If any text is unclear or unreadable in a photo, say exactly which part you
   could not read — do NOT guess what it might say.
3. Never diagnose a condition, never suggest a diagnosis, and never recommend
   a medicine for a condition.
4. Never advise a patient to change their prescribed dose, stop a medicine, or
   skip a dose — always direct them to their doctor or pharmacist for that.
5. If someone describes a medical emergency (chest pain, difficulty breathing,
   severe reaction, etc.) tell them immediately to call emergency services
   (112 in India / 911 in the US / 999 in the UK) and stop the conversation.
6. Politely decline any question that is not about understanding a medicine label
   or prescription. Say: "I'm only set up to explain medicine labels and
   prescriptions. For anything else, please speak with your doctor or pharmacist."
7. Always be warm, patient, and jargon-free. If you use a medical term,
   immediately explain it in everyday words.
8. Keep responses concise and structured — use short paragraphs or bullet points
   so the information is easy to scan.
"""

# ---------------------------------------------------------------------------
# WELCOME MESSAGE — shown to the user right after onboarding.
# {name} is replaced with the user's name at runtime.
# ---------------------------------------------------------------------------
WELCOME_MESSAGE_TEMPLATE = """
👋 Hi {name}! I'm **MedLabel**, your medicine-label assistant.

You can:
- **Type a question** about any medicine, dosage instruction, or prescription term.
- **Upload a photo** of a medicine strip, blister pack, or prescription and I'll explain what's on it.

Once we've talked about your medicines, you can tap **"📧 Email me my plan"** and I'll send a personalised Morning / Afternoon / Evening / Night reminder schedule to your inbox.

*I explain labels — I don't diagnose or change doses. Always consult your doctor or pharmacist for medical advice.*

What would you like to know? 😊
"""

# ---------------------------------------------------------------------------
# DEFAULT PHOTO PROMPT — used when the user sends a photo with no text message.
# ---------------------------------------------------------------------------
DEFAULT_PHOTO_PROMPT = (
    "The user has uploaded a photo of a medicine label, strip, blister pack, "
    "or prescription. Today's live date is {today}.\n"
    "Please:\n"
    "1. Identify the medicine name, formulation, and strength if visible.\n"
    "2. Explain the dosage and frequency instructions in plain language.\n"
    "3. List any important warnings or storage instructions shown.\n"
    "4. List the active ingredient(s) if printed.\n"
    "5. Check the expiry date printed on the label and compare it against today's date ({today}):\n"
    "   - State clearly if it is EXPIRED, EXPIRING SOON, or VALID.\n"
    "   - If expired, alert the user prominently that it has expired and should not be used.\n"
    "6. If any part of the label is unclear or unreadable, say exactly which "
    "part you could not read — do NOT guess.\n"
    "Keep the explanation friendly, concise, and easy to understand for someone with no "
    "medical background."
)

# ---------------------------------------------------------------------------
# SUMMARY REQUEST PROMPT — hidden prompt sent when the user clicks the email button.
# {today} is injected at runtime with the current date for expiry comparison.
# ---------------------------------------------------------------------------
SUMMARY_REQUEST_PROMPT_TEMPLATE = """
Based ONLY on what was discussed in this conversation, produce a structured reminder
summary in the EXACT format below. Do not invent anything not mentioned in the chat.

Today's live date is: {today}

---SESSION_SUMMARY---
Write 2-4 plain-English sentences describing:
1. What medicine(s), images, or questions the user brought to this session (e.g. "You uploaded a photo of Health OK multivitamin tablets to understand the recommended dosage and ingredients.").
2. The key findings and guidance provided regarding how to take the medicine, safety, and label instructions.
This will appear prominently at the top of their reminder email.
---END_SESSION_SUMMARY---

---MEDICINES---
For each distinct medicine discussed, output one block exactly like this:

MEDICINE_NAME: <exact name from label e.g. Health OK>
STRENGTH: <e.g. 500 mg, or formulation type like "Multivitamin & Mineral Tablets" — or "not shown" if absent>
INGREDIENTS: <key active ingredients e.g. "Taurine, Ginseng, Multivitamins, Minerals" — or "not shown">
DOSE: <e.g. 1 tablet, 5 ml — exactly as on label>
FREQUENCY: <e.g. Once daily, Twice daily — from label>
TIMING: <Morning / Afternoon / Evening / Night / Daily (any time) / Not specified on label>
WITH_FOOD: <With food / After meals / Before meals / Empty stomach / Not specified>
EXPIRY_DATE: <exact expiry date printed on label e.g. "08/2026", "Sep 2026", "15/10/2026" — write "not shown" if not visible>
EXPIRY_STATUS: <compare EXPIRY_DATE to today {today} and write exactly one of: EXPIRED | EXPIRING_SOON | VALID | UNKNOWN. EXPIRED if on or before today. EXPIRING_SOON if within 60 days of today. UNKNOWN if not shown.>
STORAGE: <storage instructions from label e.g. "Store below 25°C in a dry place" or "not shown">
WARNINGS: <key warnings or precautions from label, or "None shown">
DOCTOR_NOTE: <if timing or dose was unclear or requires medical advice, write a short note — else leave blank>

(Repeat the above block for each medicine discussed)
---END_MEDICINES---

If no medicine labels were discussed at all, write:
---NO_MEDICINES---

Only write what is explicitly shown or discussed. Never invent information.
"""
SUMMARY_REQUEST_PROMPT = SUMMARY_REQUEST_PROMPT_TEMPLATE

# ---------------------------------------------------------------------------
# SESSION CONTEXT PROMPT — fallback plain-English session summary.
# ---------------------------------------------------------------------------
SESSION_CONTEXT_PROMPT = (
    "In one short paragraph (3-4 sentences), summarise what the user discussed "
    "in this MedLabel session — which medicines or label images they uploaded or asked about, "
    "what questions they had, and any key information given. "
    "Write it warmly and clearly, as if summarising for their personal records."
)

