import streamlit as st
import pandas as pd
import openai
import os
import json
from dotenv import load_dotenv

# Load env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load data
df = pd.read_csv("all_listings_11.6.25.csv")
df.columns = [col.strip().lower() for col in df.columns]

# Set page
st.set_page_config(page_title="בוט חכם לחיפוש דירות", layout="centered")

# Session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Clear input after rerun (if needed)
if "clear_input" in st.session_state:
    st.session_state.input = ""
    del st.session_state.clear_input

# ---- STYLING ----
st.markdown("""
    <style>
    body, .stApp {
        direction: rtl;
        font-family: "Segoe UI", sans-serif;
        background-color: #121212;
        color: white;
    }

    .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2rem;
    }
    .chat-header h1 {
        font-size: 1.8rem;
        margin: 0;
    }
    .clear-button {
        background-color: #ff5252;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.3rem 1rem;
        cursor: pointer;
        font-size: 0.9rem;
    }
    .chat-bubble {
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        margin-bottom: 10px;
        max-width: 95%;
        white-space: pre-wrap;
    }
    .user-msg {
        background-color: #2e7d32;
        color: white;
        text-align: right;
    }
    .bot-msg {
        background-color: #424242;
        color: white;
        text-align: right;
    }
    .input-container {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
    }
    .send-button {
        font-size: 1.5rem;
        background-color: #1db954;
        border: none;
        color: white;
        border-radius: 50%;
        width: 45px;
        height: 45px;
        cursor: pointer;
    }
    a {
        color: #90caf9;
    }
    </style>
""", unsafe_allow_html=True)


# ---- SEARCH FUNCTION ----
def search_apartment(city=None, min_rooms=None, max_price=None, min_size=None,
                     exact_floor=None, min_floor=None, max_floor=None, apt_type=None):
    results = df.copy()

    if city:
        results = results[results['city'].str.contains(city, case=False, na=False)]

    if min_rooms:
        results = results[results['rooms'] == min_rooms]

    if max_price:
        results = results[results['price'] <= max_price]

    if min_size:
        results = results[results['size'] >= min_size]

    if exact_floor is not None:
        results = results[results['floor'] == exact_floor]
    else:
        if min_floor is not None:
            results = results[results['floor'] >= min_floor]
        if max_floor is not None:
            results = results[results['floor'] <= max_floor]

    if apt_type:
        results = results[results['apt-type'].str.contains(apt_type, case=False, na=False)]

    return results.sort_values(by="price")


# ---- MAIN UI ----
st.markdown("<div class='chat-wrapper'>", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class='chat-header'>
        <h1>🤖 בוט חכם לחיפוש דירות</h1>
    </div>
""", unsafe_allow_html=True)

if st.button("🗑️ נקה צ'אט", key="clear-chat"):
    st.session_state.chat_history = []
    st.rerun()

# Clear chat if needed
if st.session_state.get("clear") or st.query_params.get("clear"):
    st.session_state.chat_history = []

# Show messages
for msg in st.session_state.chat_history:
    role = msg["role"]
    cls = "user-msg" if role == "user" else "bot-msg"
    st.markdown(f"<div class='chat-bubble {cls}'>{msg['content']}</div>", unsafe_allow_html=True)

# --- Input area ---
with st.form(key="input_form", clear_on_submit=True):
    cols = st.columns([10, 1])
    with cols[0]:
        user_msg = st.text_input(
            "הקלד כאן",
            label_visibility="collapsed",
            placeholder="כתוב כאן את ההודעה שלך..."
        )
    with cols[1]:
        send = st.form_submit_button("←")

if send and user_msg.strip():
    user_msg = user_msg.strip()
    st.session_state.chat_history.append({"role": "user", "content": user_msg})
    st.session_state.clear_input = True  # reset flag

    messages = [{"role": "system", "content": """
    אתה בוט מומחה בחיפוש דירות להשכרה בישראל. תנהל שיחה הדרגתית עם המשתמש כדי להבין:
    עיר, מספר חדרים, תקציב מקסימלי, והעדפות נוספות.
    אם חסר מידע – שאל שאלה.
    אם יש הרבה תוצאות – שאל שאלות מצמצמות.
    אל תמציא מידע.
    אם יש את כל הנתונים הנדרשים, תבצע קריאה לפונקציית search_apartment.
    """}] + st.session_state.chat_history

    try:
        with st.spinner("🤖 חושב..."):
            res = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                functions=[{
                    "name": "search_apartment",
                    "description": "חיפוש דירות לפי סינון",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "min_rooms": {"type": "number"},
                            "max_price": {"type": "number"},
                            "min_size": {"type": "number"},
                            "exact_floor": {"type": "integer"},
                            "min_floor": {"type": "integer"},
                            "max_floor": {"type": "integer"},
                            "apt_type": {"type": "string"}
                        },
                        "required": ["city", "min_rooms", "max_price"]
                    }

                }],
                function_call="auto"
            )

            reply = res["choices"][0]["message"]

            if reply.get("function_call"):
                args = json.loads(reply["function_call"]["arguments"])
                results = search_apartment(**args)

                if len(results) == 0:
                    bot_msg = (
                        "❌ לא מצאתי דירות מתאימות לפי מה שביקשת.<br>"
                        "רוצה לנסות לחפש שוב עם טווח תקציב שונה, אזור אחר או גודל אחר?<br>"
                        "אני כאן איתך עד שנמצא משהו מתאים ✅"
                    )

                elif len(results) > 5:
                    bot_msg = f"🔎 נמצאו {len(results)} דירות... רוצה לצמצם לפי אזור/קומה/מאפיינים?"
                else:
                    links = "<br><br>".join([
                        f'''
                        🔗 <a href="{row["apt-link"]}" target="_blank">{row["address"]}</a><br>
                        💰 מחיר: {row.get("price", "לא ידוע")} ₪<br>
                        🛏️ חדרים: {row.get("rooms", "לא ידוע")}<br>
                        📏 גודל: {row.get("size", "לא ידוע")} מ"ר<br>
                        🏢 קומה: {row.get("floor", "לא ידוע")}
                        '''
                        for _, row in results.iterrows()
                    ])
                    bot_msg = (
                        f"🏠 הנה הדירות שמצאתי:<br><br>{links}<br><br>"
                        "רוצה שאחפש לך משהו אחר? אזור אחר? תקציב אחר? או שמצאת לך דירה מתאימה"
                    )

                st.session_state.chat_history.append({"role": "assistant", "content": bot_msg})
            else:
                st.session_state.chat_history.append({"role": "assistant", "content": reply["content"]})

    except Exception as e:
        st.session_state.chat_history.append({"role": "assistant", "content": f"שגיאה: {str(e)}"})

    st.rerun()


st.markdown("</div>", unsafe_allow_html=True)