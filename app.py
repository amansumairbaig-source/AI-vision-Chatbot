import json

import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient

from prompts import SUMMARY_REQUEST_PROMPT, SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE

MODEL_CANDIDATES = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.8-flash"]
MODEL_NAME = MODEL_CANDIDATES[0]


def get_secret(name):
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
TWILIO_ACCOUNT_SID = get_secret("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = get_secret("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = get_secret("TWILIO_WHATSAPP_FROM")
TWILIO_CONTENT_SID = get_secret("TWILIO_CONTENT_SID")

missing = [
    name
    for name, value in {
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "TWILIO_ACCOUNT_SID": TWILIO_ACCOUNT_SID,
        "TWILIO_AUTH_TOKEN": TWILIO_AUTH_TOKEN,
        "TWILIO_WHATSAPP_FROM": TWILIO_WHATSAPP_FROM,
        "TWILIO_CONTENT_SID": TWILIO_CONTENT_SID,
    }.items()
    if not value
]

if missing:
    st.error(
        "Missing secrets in .streamlit/secrets.toml. Copy the example file and fill in your keys before running the app."
    )
    st.stop()


@st.cache_resource
def get_gemini_client(api_key: str):
    return genai.Client(api_key=api_key)


@st.cache_resource
def get_twilio_client(account_sid: str, auth_token: str):
    return TwilioClient(account_sid, auth_token)


gemini_client = get_gemini_client(GEMINI_API_KEY)
twilio_client = get_twilio_client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def create_chat(model):
    return gemini_client.chats.create(
        model=model,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )


def ask_gemini(parts):
    last_error = ""
    # Try current model first, then any fallbacks
    models_to_try = [st.session_state.get("active_model", MODEL_NAME)] + [
        m for m in MODEL_CANDIDATES if m != st.session_state.get("active_model", MODEL_NAME)
    ]

    for model in models_to_try:
        try:
            if "chat" not in st.session_state or st.session_state.get("active_model") != model:
                st.session_state.chat = create_chat(model)
                st.session_state.active_model = model

            response = st.session_state.chat.send_message(parts)
            return response.text.strip() if getattr(response, "text", "") else "I couldn't generate a useful response."
        except Exception as error:
            last_error = str(error)
            # Reset chat to try next model
            st.session_state.chat = None
            if "API_KEY_INVALID" in last_error or "API key not valid" in last_error:
                return (
                    "⚠️ **Invalid Gemini API Key**: The API key in `.streamlit/secrets.toml` is invalid or still set to demo. "
                    "Please get a free key from https://aistudio.google.com/app/apikey, update `.streamlit/secrets.toml`, "
                    "save the file, and click 'Reset Session' in the sidebar."
                )

    return f"Sorry, something went wrong: {last_error}"


def clean_whatsapp_text(text):
    if not text:
        return "No nutrition summary available."

    cleaned = " ".join(text.split())
    return cleaned[:1500] + "..." if len(cleaned) > 1500 else cleaned


def send_whatsapp(to_number, user_name, summary):
    try:
        content_variables = json.dumps(
            {"1": user_name, "2": clean_whatsapp_text(summary)},
            ensure_ascii=False,
        )

        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            content_sid=TWILIO_CONTENT_SID,
            content_variables=content_variables,
        )

        return True, message.sid
    except Exception as error:
        return False, str(error)


if "onboarded" not in st.session_state:
    st.title("🥗 MacroSnap")
    st.caption("Snap it. Track it. Text yourself the results.")

    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
            help="This is the number MacroSnap will text your summary to.",
        )
        submitted = st.form_submit_button("Let's go 🚀")

    if submitted:
        if not name.strip() or not whatsapp_number.strip():
            st.warning("Please fill in both your name and WhatsApp number.")
        else:
            st.session_state.name = name.strip()
            st.session_state.whatsapp_number = whatsapp_number.strip()
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.active_model = MODEL_NAME
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()

    st.stop()

with st.sidebar:
    st.header("⚙️ MacroSnap Settings")
    st.write(f"👤 **User:** {st.session_state.name}")
    st.write(f"📱 **WhatsApp:** {st.session_state.whatsapp_number}")
    st.divider()
    if st.button("🔄 Reset Session / Clear Chat", use_container_width=True):
        st.session_state.clear()
        st.rerun()

header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("🥗 MacroSnap")

with button_col:
    send_disabled = len(st.session_state.get("messages", [])) <= 2
    if st.button("📤 Send to WhatsApp", disabled=send_disabled, use_container_width=True):
        with st.spinner("Summarizing your day..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])

        success, info = send_whatsapp(
            st.session_state.whatsapp_number,
            st.session_state.name,
            summary,
        )

        if success:
            st.success("Sent! Check your WhatsApp 📲")
        else:
            st.error(f"Couldn't send that: {info}")

st.caption(f"Logged in as {st.session_state.name} • updates go to {st.session_state.whatsapp_number}")

if not st.session_state.get("messages"):
    st.session_state.messages = []
    st.session_state.messages.append(
        {"role": "assistant", "kind": "text", "content": WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name)}
    )
    render_message(st.session_state.messages[-1])
else:
    for message in st.session_state.messages:
        render_message(message)

user_input = st.chat_input(
    "Ask a question, or attach a photo of your meal",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text or ""
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))

    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("What is this meal? Give me the calories and macros.")

    with st.spinner("Crunching the numbers..."):
        answer = ask_gemini(parts)

    add_message("assistant", "text", answer)
