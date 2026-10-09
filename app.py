import calendar
import re
import smtplib
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st
from google import genai
from google.genai import types

from prompts import (
    DEFAULT_PHOTO_PROMPT,
    SESSION_CONTEXT_PROMPT,
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
)

try:
    from prompts import SUMMARY_REQUEST_PROMPT_TEMPLATE
except ImportError:
    from prompts import SUMMARY_REQUEST_PROMPT as SUMMARY_REQUEST_PROMPT_TEMPLATE



MODEL_NAME = "gemini-3.8-flash"
st.set_page_config(page_title="MedLabel", page_icon="💊")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
GMAIL_ADDRESS = st.secrets["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]

# ---------- Theme: dark + light (black / grey / white) ----------
THEMES = {
    "dark": {
        "scheme": "dark",
        "bg": "#212121",
        "panel": "#303030",
        "panel-2": "#292929",
        "border": "#424242",
        "focus": "#6E6E6E",
        "text": "#ECECEC",
        "muted": "#B4B4B4",
        "placeholder": "#9B9B9B",
        "shadow": "0 2px 14px rgba(0, 0, 0, 0.28)",
        "btn-bg": "#FFFFFF",
        "btn-text": "#0D0D0D",
        "btn-hover": "#D9D9D9",
        "btn-off-bg": "#383838",
        "btn-off-text": "#808080",
        "switch-track": "#5A5A5A",
        "switch-left": "27px",
    },
    "light": {
        "scheme": "light",
        "bg": "#FFFFFF",
        "panel": "#E8E8E8",      # input field bg — clearly visible on white page
        "panel-2": "#F5F5F5",  # form card bg — slightly off-white
        "border": "#D4D4D4",
        "focus": "#A6A6A6",
        "text": "#0D0D0D",
        "muted": "#5D5D5D",
        "placeholder": "#737373",
        "shadow": "0 2px 14px rgba(0, 0, 0, 0.07)",
        "btn-bg": "#0D0D0D",
        "btn-text": "#FFFFFF",
        "btn-hover": "#3A3A3A",
        "btn-off-bg": "#E0E0E0",
        "btn-off-text": "#9A9A9A",
        "switch-track": "#CFCFCF",
        "switch-left": "3px",
    },
}

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

palette = THEMES[st.session_state.theme]
root_vars = "; ".join(f"--{key}: {value}" for key, value in palette.items() if key != "scheme")
st.markdown(
    f"<style>:root {{ {root_vars}; color-scheme: {palette['scheme']}; }}</style>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
    }
    #MainMenu, footer {visibility: hidden;}
    [data-testid="stHeader"] {background: transparent !important;}
    .block-container {max-width: 740px; padding-top: 2.2rem; padding-bottom: 6rem;}

    /* ---- Text ---- */
    .stApp h1 {
        color: var(--text) !important; font-weight: 700;
        letter-spacing: -0.8px; font-size: 2rem; padding: 0;
    }
    .stApp .stMarkdown, .stApp .stMarkdown p,
    .stApp [data-testid="stChatMessage"] p,
    .stApp [data-testid="stChatMessage"] li,
    .stApp [data-testid="stSpinner"] p,
    .stApp [data-testid="stAlert"] p {color: var(--text) !important; line-height: 1.65;}
    .stApp [data-testid="stWidgetLabel"] p {
        color: var(--text) !important; font-weight: 500; font-size: 0.9rem;
    }
    .stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p {
        color: var(--muted) !important;
    }

    /* ---- Onboarding form card ---- */
    [data-testid="stForm"] {
        background: var(--panel-2);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 1.8rem 1.6rem;
    }

    /* ---- Text inputs: one clean box, one border ---- */
    .stTextInput [data-baseweb="input"] {
        background: var(--panel) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        min-height: 50px;
        box-shadow: none !important;
        transition: border-color 0.15s;
    }
    .stTextInput [data-baseweb="input"]:hover {border-color: var(--focus) !important;}
    .stTextInput [data-baseweb="input"]:focus-within {
        border-color: var(--focus) !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .stTextInput [data-baseweb="base-input"] {
        background: transparent !important; border: none !important; box-shadow: none !important;
    }
    .stTextInput input {
        background: transparent !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        caret-color: var(--text);
        font-size: 0.98rem;
        padding: 0.75rem 1rem !important;
        border: none !important; box-shadow: none !important; outline: none !important;
    }
    .stTextInput input::placeholder {
        color: var(--placeholder) !important;
        -webkit-text-fill-color: var(--placeholder) !important;
        opacity: 1 !important;
    }
    .stTextInput input:-webkit-autofill {
        -webkit-box-shadow: 0 0 0 1000px var(--panel) inset !important;
        -webkit-text-fill-color: var(--text) !important;
    }
    [data-testid="InputInstructions"] {color: var(--muted) !important;}
    [data-testid="stTooltipIcon"] svg {color: var(--muted) !important;}

    /* ---- Buttons ---- */
    .stButton > button, [data-testid="stFormSubmitButton"] > button {
        background-color: var(--btn-bg) !important;
        color: var(--btn-text) !important;
        border: 1px solid var(--btn-bg) !important;
        border-radius: 999px;
        font-weight: 600;
        min-height: 46px;
        transition: background-color 0.15s, transform 0.05s;
    }
    .stButton > button p, [data-testid="stFormSubmitButton"] > button p {
        color: var(--btn-text) !important; font-weight: 600;
    }
    .stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
        background-color: var(--btn-hover) !important;
        border-color: var(--btn-hover) !important;
    }
    .stButton > button:active, [data-testid="stFormSubmitButton"] > button:active {transform: scale(0.98);}
    .stButton > button:disabled {
        background-color: var(--btn-off-bg) !important;
        border-color: var(--btn-off-bg) !important;
    }
    .stButton > button:disabled p {color: var(--btn-off-text) !important;}

    /* ---- Theme switch (sliding toggle, like other apps) ---- */
    .st-key-theme_toggle button, .st-key-theme_toggle_chat button {
        position: relative;
        width: 56px; min-width: 56px; height: 30px; min-height: 30px; padding: 0;
        border-radius: 999px !important;
        background-color: var(--switch-track) !important;
        border: 1px solid var(--border) !important;
        transition: background-color 0.2s;
    }
    .st-key-theme_toggle button p, .st-key-theme_toggle_chat button p {
        font-size: 0 !important; line-height: 0;   /* hide label text, keep it for screen readers */
    }
    .st-key-theme_toggle button::after, .st-key-theme_toggle_chat button::after {
        content: "";
        position: absolute; top: 3px; left: var(--switch-left);
        width: 22px; height: 22px; border-radius: 50%;
        background: #FFFFFF;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.35);
        transition: left 0.2s ease;
    }
    .st-key-theme_toggle button:hover, .st-key-theme_toggle_chat button:hover {
        background-color: var(--switch-track) !important; border-color: var(--focus) !important;
    }

    /* ---- Chat messages ---- */
    [data-testid="stChatMessage"] {background: transparent; padding: 0.7rem 0;}
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        background: var(--panel);
        border-radius: 20px;
        padding: 0.8rem 1.1rem;
        margin-left: 14%;
    }
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"] {
        background: var(--panel) !important; color: var(--text) !important;
        border: 1px solid var(--border);
    }
    [data-testid="stChatMessage"] img {border-radius: 14px;}

    /* ---- Chat input bar (ChatGPT-style composer) ---- */
    [data-testid="stBottom"], [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {background: var(--bg) !important;}
    [data-testid="stChatInput"] {
        background: var(--panel) !important;
        border: 1px solid var(--border) !important;
        border-radius: 28px !important;
        box-shadow: var(--shadow);
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: var(--focus) !important;
    }
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] [data-baseweb="textarea"],
    [data-testid="stChatInput"] [data-baseweb="base-input"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        caret-color: var(--text);
        outline: none !important; box-shadow: none !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--placeholder) !important;
        -webkit-text-fill-color: var(--placeholder) !important;
        opacity: 1 !important;
    }
    [data-testid="stChatInput"] span, [data-testid="stChatInput"] small {color: var(--text) !important;}
    [data-testid="stChatInput"] [data-testid*="File"] {
        background: var(--panel-2) !important; color: var(--text) !important;
    }
    [data-testid="stChatInput"] button {background: transparent !important; color: var(--text) !important;}
    [data-testid="stChatInput"] button svg {fill: currentColor !important; color: inherit !important;}
    [data-testid="stChatInput"] [data-testid="stChatInputSubmitButton"] {
        background: var(--btn-bg) !important; color: var(--btn-text) !important; border-radius: 50%;
    }

    /* ---- Alerts + safety note ---- */
    [data-testid="stAlert"] {
        background: var(--panel) !important;
        border: 1px solid var(--border); border-radius: 14px;
    }
    .safety-note {
        background: var(--panel-2); border: 1px solid var(--border);
        border-radius: 14px; padding: 0.65rem 1rem;
        color: var(--muted); font-size: 0.85rem; margin: 0.6rem 0 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def theme_toggle(key):
    """Sliding switch that flips between dark and light mode."""
    is_dark = st.session_state.theme == "dark"
    if st.button("Toggle theme", key=key, help="Switch to light mode" if is_dark else "Switch to dark mode"):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()


# ---------- Gemini + helpers ----------
@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"], width=260)


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry, something went wrong: {error}"


def is_valid_email(address):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", address) is not None


def _parse_gemini_summary(raw: str) -> tuple[str, list[dict]]:
    """Parse structured Gemini output into (session_summary, list_of_medicine_dicts)."""
    session_summary = ""
    medicines = []

    ss_match = re.search(r"---SESSION_SUMMARY---(.*?)---END_SESSION_SUMMARY---", raw, re.DOTALL)
    if ss_match:
        session_summary = ss_match.group(1).strip()

    med_match = re.search(r"---MEDICINES---(.*?)---END_MEDICINES---", raw, re.DOTALL)
    if med_match:
        block = med_match.group(1).strip()
        for chunk in re.split(r"\n{2,}", block):
            med: dict = {}
            for line in chunk.strip().splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    med[key.strip().upper()] = val.strip()
            if "MEDICINE_NAME" in med:
                medicines.append(med)

    return session_summary, medicines


def parse_expiry_live(expiry_raw: str, fallback_status: str = "UNKNOWN", today: date = None) -> tuple[str, str, str]:
    """
    Deterministically computes live expiry status against today's date.
    Returns: (status, human_readable_description, formatted_date_string)
    status is one of: 'EXPIRED', 'EXPIRING_SOON', 'VALID', 'UNKNOWN'
    """
    if today is None:
        today = date.today()

    if not expiry_raw or expiry_raw.strip().lower() in ("not shown", "unknown", "none", "n/a", "none shown", ""):
        return "UNKNOWN", "Not visible on label &mdash; verify outer pack before taking", "Not visible"

    cleaned = re.sub(r"^(exp|expiry|exp date|best before|bb)[:.\s]*", "", expiry_raw, flags=re.I).strip()
    exp_date = None

    # Pattern 1: MM/YYYY or MM/YY or MM-YYYY or MM.YYYY
    m = re.search(r"\b(0[1-9]|1[0-2])[\/\-\.](20\d{2}|\d{2})\b", cleaned)
    if m:
        month = int(m.group(1))
        yr = int(m.group(2))
        if yr < 100:
            yr += 2000
        last_day = calendar.monthrange(yr, month)[1]
        exp_date = date(yr, month, last_day)

    # Pattern 2: Month Name YYYY or Month YY (e.g. Aug 2026, September 2026)
    if not exp_date:
        for fmt in ("%b %Y", "%B %Y", "%b-%Y", "%B-%Y", "%b/%Y", "%b %y", "%b-%y"):
            m2 = re.search(r"\b([A-Za-z]{3,9})[\s\-\/]+(20\d{2}|\d{2})\b", cleaned)
            if m2:
                try:
                    dt = datetime.strptime(f"{m2.group(1)} {m2.group(2)}", "%b %Y" if len(m2.group(2)) == 4 else "%b %y")
                    last_day = calendar.monthrange(dt.year, dt.month)[1]
                    exp_date = date(dt.year, dt.month, last_day)
                    break
                except Exception:
                    pass

    # Pattern 3: DD/MM/YYYY or DD-MM-YYYY
    if not exp_date:
        m3 = re.search(r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](20\d{2}|\d{2})\b", cleaned)
        if m3:
            d, m_val, yr = int(m3.group(1)), int(m3.group(2)), int(m3.group(3))
            if yr < 100:
                yr += 2000
            try:
                exp_date = date(yr, m_val, d)
            except Exception:
                pass

    if exp_date:
        formatted_exp = exp_date.strftime("%d %b %Y")
        if exp_date < today:
            delta = (today - exp_date).days
            time_str = f"{delta} day" if delta == 1 else f"{delta} days" if delta < 60 else f"{delta // 30} month(s)"
            return "EXPIRED", f"Expired on {formatted_exp} ({time_str} ago) &mdash; DO NOT USE", formatted_exp
        elif 0 <= (exp_date - today).days <= 60:
            delta = (exp_date - today).days
            return "EXPIRING_SOON", f"Expiring soon on {formatted_exp} (in {delta} days) &mdash; Refill advised", formatted_exp
        else:
            return "VALID", f"Valid until {formatted_exp} (Safe to use)", formatted_exp

    fb = fallback_status.strip().upper() if fallback_status else "UNKNOWN"
    if fb in ("EXPIRED", "EXPIRING_SOON", "VALID"):
        labels = {
            "EXPIRED": f"Expired ({cleaned}) &mdash; DO NOT USE",
            "EXPIRING_SOON": f"Expiring soon ({cleaned}) &mdash; Refill advised",
            "VALID": f"Valid ({cleaned})",
        }
        return fb, labels[fb], cleaned

    return "UNKNOWN", f"{cleaned} (Not verified against calendar)", cleaned


def _expiry_badge(status: str, desc: str) -> str:
    """Return an inline HTML badge for live expiry status."""
    cfg = {
        "EXPIRED":       ("#dc2626", "#fee2e2", "#b91c1c", "&#10006; EXPIRED"),
        "EXPIRING_SOON": ("#d97706", "#fef3c7", "#b45309", "&#9888; EXPIRING SOON"),
        "VALID":         ("#16a34a", "#dcfce7", "#15803d", "&#10003; VALID"),
        "UNKNOWN":       ("#64748b", "#f1f5f9", "#475569", "&#128269; UNVERIFIED"),
    }
    border_col, bg_col, text_col, tag_label = cfg.get(status.upper(), cfg["UNKNOWN"])
    return (
        f'<span style="display:inline-block;background:{bg_col};border:1px solid {border_col};'
        f'border-radius:6px;padding:3px 9px;vertical-align:middle;">'
        f'<strong style="font-size:11px;color:{text_col};letter-spacing:0.4px;">{tag_label}</strong>'
        f'<span style="font-size:12px;color:#1e293b;font-weight:600;margin-left:6px;">&bull; {desc}</span>'
        f'</span>'
    )


def _build_html_email(user_name: str, session_summary: str, medicines: list[dict]) -> str:
    """Render a pixel-perfect, highly responsive HTML email with live expiry calculations."""
    today_obj = date.today()
    today_str = today_obj.strftime("%d %B %Y")
    day_name = today_obj.strftime("%A, %d %B %Y")

    # 1. Process and compute live expiry for every medicine
    for m in medicines:
        raw_exp = m.get("EXPIRY_DATE", "not shown")
        raw_stat = m.get("EXPIRY_STATUS", "UNKNOWN")
        status, desc, fmt_date = parse_expiry_live(raw_exp, raw_stat, today=today_obj)
        m["_live_status"] = status
        m["_live_desc"] = desc
        m["_live_date"] = fmt_date

    expired_items = [m for m in medicines if m.get("_live_status") == "EXPIRED"]
    expiring_soon_items = [m for m in medicines if m.get("_live_status") == "EXPIRING_SOON"]

    # 2. Expiry alert banner (if any expired or expiring soon)
    expiry_banner = ""
    if expired_items:
        names_str = ", ".join(f"<strong>{m.get('MEDICINE_NAME', 'Medicine')}</strong> ({m.get('_live_desc', '')})" for m in expired_items)
        expiry_banner = f"""
        <tr>
          <td style="padding:0 32px 18px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:#fef2f2;border:1px solid #f87171;border-left:5px solid #dc2626;
                          border-radius:10px;overflow:hidden;">
              <tr>
                <td style="padding:14px 18px;">
                  <p style="margin:0 0 5px;font-size:13px;font-weight:700;color:#991b1b;letter-spacing:0.3px;">
                    &#9888; CRITICAL ALERT: EXPIRED MEDICINE DETECTED
                  </p>
                  <p style="margin:0;font-size:13px;color:#7f1d1d;line-height:1.55;">
                    As of today's live date (<strong>{today_str}</strong>), the following item is expired:
                    <br>{names_str}.
                    <br><span style="display:inline-block;margin-top:5px;font-weight:600;">
                    Do not take this medication. Expired medicines may lose efficacy or cause adverse effects. Please consult your pharmacist for a fresh replacement.
                    </span>
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>"""
    elif expiring_soon_items:
        names_str = ", ".join(f"<strong>{m.get('MEDICINE_NAME', 'Medicine')}</strong> ({m.get('_live_desc', '')})" for m in expiring_soon_items)
        expiry_banner = f"""
        <tr>
          <td style="padding:0 32px 18px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:#fffbeb;border:1px solid #fcd34d;border-left:5px solid #d97706;
                          border-radius:10px;overflow:hidden;">
              <tr>
                <td style="padding:14px 18px;">
                  <p style="margin:0 0 5px;font-size:13px;font-weight:700;color:#92400e;letter-spacing:0.3px;">
                    &#9888; NOTICE: MEDICINE EXPIRING SOON
                  </p>
                  <p style="margin:0;font-size:13px;color:#78350f;line-height:1.55;">
                    The following medication will expire soon: {names_str}. Please plan to refill your prescription before this date.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>"""

    # 3. Dynamic Daily Routine Timeline (NO empty slots)
    slot_buckets = {
        "Morning": [],
        "Afternoon": [],
        "Evening": [],
        "Night": [],
        "Daily / Flexible": []
    }
    for m in medicines:
        tim = m.get("TIMING", "").lower()
        if "morn" in tim or "breakfast" in tim or "am" in tim:
            slot_buckets["Morning"].append(m)
        elif "afternoon" in tim or "lunch" in tim or "noon" in tim:
            slot_buckets["Afternoon"].append(m)
        elif "even" in tim or "dusk" in tim:
            slot_buckets["Evening"].append(m)
        elif "night" in tim or "bed" in tim or "dinner" in tim:
            slot_buckets["Night"].append(m)
        else:
            slot_buckets["Daily / Flexible"].append(m)

    slot_meta = {
        "Morning": ("&#9728; Morning", "#b45309", "#fffbeb", "#fde68a"),
        "Afternoon": ("&#127780; Afternoon", "#0369a1", "#f0f9ff", "#bae6fd"),
        "Evening": ("&#127769; Evening", "#6d28d9", "#f5f3ff", "#ddd6fe"),
        "Night": ("&#127756; Night", "#334155", "#f8fafc", "#e2e8f0"),
        "Daily / Flexible": ("&#128203; Daily / Flexible Routine", "#047857", "#ecfdf5", "#a7f3d0"),
    }

    routine_rows = ""
    for slot_name, items in slot_buckets.items():
        if not items:
            continue
        label, text_color, bg_color, border_color = slot_meta[slot_name]
        item_bullets = []
        for it in items:
            name = it.get("MEDICINE_NAME", "Medicine")
            dose = it.get("DOSE", "1 dose")
            freq = it.get("FREQUENCY", "")
            food = it.get("WITH_FOOD", "")
            details = [dose]
            if freq and freq.lower() not in ("not shown", "none", "blank"):
                details.append(freq)
            if food and food.lower() not in ("not specified", "not shown", "none", "blank"):
                details.append(food)
            detail_str = f" &bull; {', '.join(details)}" if details else ""
            item_bullets.append(f"<strong>{name}</strong>{detail_str}")

        routine_rows += f"""
        <tr>
          <td style="padding:6px 0;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:{bg_color};border:1px solid {border_color};border-radius:8px;padding:9px 14px;">
              <tr>
                <td width="150" style="width:150px;min-width:150px;font-size:12px;font-weight:700;color:{text_color};
                           vertical-align:middle;text-transform:uppercase;letter-spacing:0.5px;">
                  {label}
                </td>
                <td style="font-size:13px;color:#0f172a;vertical-align:middle;line-height:1.5;">
                  {'<br>'.join(item_bullets)}
                </td>
              </tr>
            </table>
          </td>
        </tr>"""

    routine_section = ""
    if routine_rows:
        routine_section = f"""
        <!-- ═══ DAILY ROUTINE OVERVIEW ═══ -->
        <tr>
          <td style="padding:0 32px 18px;">
            <p style="margin:0 0 8px;font-size:11px;font-weight:700;color:#64748b;
                      letter-spacing:1px;text-transform:uppercase;">
              Daily Routine Overview
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              {routine_rows}
            </table>
          </td>
        </tr>"""

    # 4. Helper for pixel-perfect detail rows
    def detail_row(label: str, value: str, custom_color: str = None) -> str:
        skip = ("", "not shown", "none shown", "blank", "n/a", "none")
        if not value or value.strip().lower() in skip:
            return ""
        val_col = custom_color or "#0f172a"
        return f"""
        <tr>
          <td width="145" style="width:145px;min-width:145px;padding:8px 12px 8px 0;vertical-align:middle;
                     font-size:11.5px;font-weight:700;color:#64748b;
                     text-transform:uppercase;letter-spacing:0.5px;
                     border-bottom:1px solid #f1f5f9;">
            {label}
          </td>
          <td style="padding:8px 0;vertical-align:middle;font-size:13.5px;
                     color:{val_col};font-weight:500;line-height:1.5;
                     border-bottom:1px solid #f1f5f9;">
            {value}
          </td>
        </tr>"""

    # 5. Build one rich card per medicine
    all_med_html = ""
    for idx, m in enumerate(medicines):
        name_str    = m.get("MEDICINE_NAME", "Unknown Medicine")
        timing      = m.get("TIMING", "Not specified on label")
        doctor_note = m.get("DOCTOR_NOTE", "").strip()
        warnings    = m.get("WARNINGS", "").strip()
        storage     = m.get("STORAGE", "").strip()
        ingredients = m.get("INGREDIENTS", "").strip()
        status      = m.get("_live_status", "UNKNOWN")
        desc        = m.get("_live_desc", "Not visible on label")

        warn_color = "#dc2626" if status == "EXPIRED" else "#b45309" if warnings.lower() not in ("none shown", "not shown", "") else "#0f172a"

        timing_badge = (
            f'<span style="display:inline-block;background:#f1f5f9;border:1px solid #cbd5e1;'
            f'border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700;color:#334155;">'
            f'{timing}</span>'
        )

        doctor_html = ""
        if doctor_note and doctor_note.lower() not in ("none", "none shown", "blank"):
            doctor_html = f"""
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="margin-top:12px;background:#fefce8;border:1px solid #fef08a;
                          border-left:4px solid #ca8a04;border-radius:6px;padding:9px 12px;">
              <tr>
                <td style="font-size:12.5px;color:#854d0e;line-height:1.5;">
                  &#129658; <strong>Healthcare Advice:</strong> {doctor_note}
                </td>
              </tr>
            </table>"""

        all_med_html += f"""
        <!-- Medicine Card {idx + 1} -->
        <table width="100%" cellpadding="0" cellspacing="0" border="0"
               style="border:1px solid #e2e8f0;border-radius:12px;margin-bottom:18px;
                      background:#ffffff;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.03);">
          <!-- Header -->
          <tr>
            <td style="padding:14px 18px 12px;background:#f8fafc;border-bottom:1px solid #e2e8f0;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td style="font-size:15px;font-weight:700;color:#0f172a;vertical-align:middle;">
                    &#128138; {name_str}
                  </td>
                  <td align="right" style="vertical-align:middle;white-space:nowrap;">
                    {timing_badge}
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:10px 18px 14px;">
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                {detail_row('Form / Strength', m.get('STRENGTH', ''))}
                {detail_row('Active Ingredients', ingredients)}
                {detail_row('Recommended Dose', m.get('DOSE', ''))}
                {detail_row('Frequency', m.get('FREQUENCY', ''))}
                {detail_row('Take with food', m.get('WITH_FOOD', ''))}
                <tr>
                  <td width="145" style="width:145px;min-width:145px;padding:8px 12px 8px 0;vertical-align:middle;
                             font-size:11.5px;font-weight:700;color:#64748b;
                             text-transform:uppercase;letter-spacing:0.5px;
                             border-bottom:1px solid #f1f5f9;">
                    Live Expiry Check
                  </td>
                  <td style="padding:8px 0;vertical-align:middle;border-bottom:1px solid #f1f5f9;">
                    {_expiry_badge(status, desc)}
                  </td>
                </tr>
                {detail_row('Storage', storage)}
                {detail_row('Warnings', warnings, warn_color)}
              </table>
              {doctor_html}
            </td>
          </tr>
        </table>"""

    if not all_med_html:
        all_med_html = (
            '<p style="font-size:14px;color:#94a3b8;margin:0;">'
            "No medicine labels were discussed in this session.</p>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your MedLabel Reminder Plan</title>
</head>
<body style="margin:0;padding:0;background-color:#f8fafc;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
             color:#0f172a;">

  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f8fafc;">
    <tr><td align="center" style="padding:32px 16px;">

      <!-- Email card container -->
      <table width="600" cellpadding="0" cellspacing="0" border="0"
             style="max-width:600px;width:100%;background:#ffffff;
                    border-radius:16px;overflow:hidden;
                    border:1px solid #e2e8f0;box-shadow:0 4px 14px rgba(0,0,0,0.05);">

        <!-- ═══ HEADER ═══ -->
        <tr>
          <td style="background:#0f172a;padding:26px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td>
                  <p style="margin:0;font-size:26px;line-height:1;">&#128138;</p>
                  <h1 style="margin:6px 0 2px;font-size:22px;font-weight:700;
                             color:#ffffff;letter-spacing:-0.4px;">MedLabel</h1>
                  <p style="margin:0;font-size:12.5px;color:#94a3b8;">
                    Personalised Medicine Guide &amp; Reminder Plan
                  </p>
                </td>
                <td align="right" style="vertical-align:top;">
                  <span style="display:inline-block;background:#1e293b;border:1px solid #334155;
                               border-radius:6px;padding:4px 10px;text-align:right;">
                    <span style="display:block;font-size:10.5px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">Live Analysis Date</span>
                    <strong style="display:block;font-size:12px;color:#f8fafc;">{day_name}</strong>
                  </span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ═══ GREETING & SESSION CONTEXT ═══ -->
        <tr>
          <td style="padding:24px 32px 18px;">
            <h2 style="margin:0 0 12px;font-size:19px;color:#0f172a;font-weight:700;">
              Hi {user_name}! &#128075;
            </h2>
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:#f0f9ff;border:1px solid #bae6fd;border-left:4px solid #0284c7;
                          border-radius:8px;padding:14px 16px;">
              <tr>
                <td>
                  <p style="margin:0 0 5px;font-size:11px;font-weight:700;color:#0369a1;
                             letter-spacing:0.8px;text-transform:uppercase;">
                    &#128203; Session Context &amp; Label Findings
                  </p>
                  <p style="margin:0;font-size:13.5px;color:#1e293b;line-height:1.65;">
                    {session_summary or 'Here is your personalized medicine summary based on what was discussed.'}
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        {expiry_banner}

        {routine_section}

        <!-- ═══ MEDICINE DETAILS ═══ -->
        <tr>
          <td style="padding:0 32px 8px;">
            <p style="margin:0 0 10px;font-size:11px;font-weight:700;color:#64748b;
                      letter-spacing:1px;text-transform:uppercase;">
              Verified Medicine Details
            </p>
            {all_med_html}
          </td>
        </tr>

        <!-- ═══ MEDICAL DISCLAIMER ═══ -->
        <tr>
          <td style="padding:8px 32px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:12px 16px;">
              <tr>
                <td>
                  <p style="margin:0;font-size:12px;color:#991b1b;line-height:1.6;">
                    <strong>&#9888; Medical Disclaimer:</strong> This plan is based solely on
                    information extracted from visible text on your medicine labels. It is <strong>not</strong> a substitute for professional medical diagnosis or treatment.
                    Always follow your doctor's or pharmacist's exact instructions.
                    In an emergency, call <strong>112</strong> (India) / <strong>911</strong> (US) / <strong>999</strong> (UK).
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ═══ FOOTER ═══ -->
        <tr>
          <td style="background:#f8fafc;padding:16px 32px;border-top:1px solid #e2e8f0;">
            <p style="margin:0;font-size:11.5px;color:#94a3b8;text-align:center;line-height:1.6;">
              Sent by <strong style="color:#475569;">&#128138; MedLabel</strong>
              &nbsp;&bull;&nbsp; Powered by Gemini 3.8 Flash
              &nbsp;&bull;&nbsp; Live Date: {today_str}
            </p>
          </td>
        </tr>

      </table>
      <!-- /Email card container -->

    </td></tr>
  </table>
  <!-- /Outer wrapper -->

</body>
</html>"""


def send_email(to_address: str, user_name: str, html_body: str) -> tuple[bool, str | None]:
    """Send a rich HTML email via Gmail SMTP-SSL."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "\U0001f48a Your MedLabel Reminder Plan"
        msg["From"] = GMAIL_ADDRESS
        msg["To"] = to_address
        plain = (
            "Your MedLabel reminder plan is ready. "
            "Please open this email in an HTML-capable email client to view the full plan."
        )
        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        return True, None
    except Exception as error:
        return False, str(error)


# Step 1: onboarding
if "onboarded" not in st.session_state:
    title_col, toggle_col = st.columns([8, 1], vertical_alignment="center")
    with title_col:
        st.title("💊 MedLabel")
    with toggle_col:
        theme_toggle("theme_toggle")
    st.caption("Snap it. Understand it. Email yourself the plan.")
    with st.form("onboarding_form"):
        name = st.text_input("Your name", placeholder="e.g. Asha")
        email = st.text_input(
            "Your email address",
            placeholder="you@example.com",
            help="This is where MedLabel will send your reminder plan.",
        )
        submitted = st.form_submit_button("Let's go 🚀", use_container_width=True)
    if submitted:
        if not name.strip() or not email.strip():
            st.warning("Please fill in both your name and email.")
        elif not is_valid_email(email.strip()):
            st.warning("That email doesn't look right. Please check it.")
        else:
            st.session_state.name = name.strip()
            st.session_state.email = email.strip()
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()
    st.stop()

# Step 2: chat interface
header_col, button_col, toggle_col = st.columns([5, 3, 1], vertical_alignment="center")

with header_col:
    st.title("💊 MedLabel")

with button_col:
    has_user_chatted = any(m.get("role") == "user" for m in st.session_state.get("messages", []))
    send_disabled = not has_user_chatted
    if st.button("\U0001f4e7 Email my plan", disabled=send_disabled, use_container_width=True):
        today_str = date.today().strftime("%d %B %Y")   # e.g. 09 October 2026
        prompt = SUMMARY_REQUEST_PROMPT_TEMPLATE.replace("{today}", today_str)
        with st.spinner("Analysing your session..."):
            raw_summary = ask_gemini([prompt])
        session_summary, medicines = _parse_gemini_summary(raw_summary)
        if not session_summary:
            session_summary = ask_gemini([SESSION_CONTEXT_PROMPT])
        html_body = _build_html_email(st.session_state.get("name", ""), session_summary, medicines)
        with st.spinner("Sending to your inbox..."):
            success, info = send_email(st.session_state.get("email", ""), st.session_state.get("name", ""), html_body)
        if success:
            st.success("Plan sent! Check your inbox (or spam) \U0001f4ec")
            st.session_state.messages.append({
                "role": "assistant",
                "kind": "text",
                "content": f"\U0001f4ec **Your reminder plan has been emailed to `{st.session_state.get('email', '')}`!** Please check your inbox (or spam folder)."
            })
            st.rerun()
        else:
            st.error(f"Failed to send email: {info}")


with toggle_col:
    theme_toggle("theme_toggle_chat")

user_name = st.session_state.get("name", "")
user_email = st.session_state.get("email", "")
st.caption(f"Logged in as {user_name} - plan goes to {user_email}")
st.markdown(
    '<div class="safety-note">⚕️ General information only - not medical advice. '
    "Always follow your doctor&#39;s prescription.</div>",
    unsafe_allow_html=True,
)

if not st.session_state.get("messages", []):
    add_message("assistant", "text", WELCOME_MESSAGE_TEMPLATE.format(name=user_name))
else:
    for message in st.session_state.get("messages", []):
        render_message(message)

user_input = st.chat_input(
    "Attach a clear photo of your medicine, or ask a question",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []
    today_str = date.today().strftime("%d %B %Y")

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append(DEFAULT_PHOTO_PROMPT.format(today=today_str))

    with st.spinner("Reading the label..."):
        answer = ask_gemini(parts)
    st.session_state.messages.append({"role": "assistant", "kind": "text", "content": answer})
    st.rerun()