import streamlit as st
import google.generativeai as genai
import time
import pandas as pd # Data handle karne ke liye

# --- CONFIGURATION ---
st.set_page_config(page_title="CGC Smart-Eat", page_icon="🦁", layout="centered")

# ⚠️ APNI API KEY YAHAN DAAL
GOOGLE_API_KEY = "YOUR_API_KEY_HERE"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    ai_available = True
except:
    ai_available = False

# --- MENUS ---
MENUS = {
    "Main Canteen 🍛": {"Rajma Chawal": 450, "Thali": 700, "Samosa": 250},
    "Nescafe ☕": {"Cold Coffee": 300, "Grilled Sandwich": 350, "Maggi": 400},
    "Subway 🥪": {"Veggie Delite": 230, "Paneer Tikka": 350, "Cookie": 200}
}
PRICES = { # Dummy Prices
    "Rajma Chawal": 50, "Thali": 60, "Samosa": 15, "Cold Coffee": 40,
    "Grilled Sandwich": 60, "Maggi": 30, "Veggie Delite": 120, 
    "Paneer Tikka": 150, "Cookie": 50
}

# --- SESSION STATE (Database) ---
if 'page' not in st.session_state: st.session_state.page = 'home'
if 'health_score' not in st.session_state: st.session_state.health_score = 85
if 'recovery_plan' not in st.session_state: st.session_state.recovery_plan = "Drink 2L water today."
if 'order_history' not in st.session_state: 
    # Dummy Start Data
    st.session_state.order_history = [
        {"item": "Fruit Salad", "cals": 100, "time": "Yesterday", "ai_msg": "Good job!"}
    ]
if 'total_cals_today' not in st.session_state: st.session_state.total_cals_today = 0

# --- NAVIGATION ---
def go_to(page):
    st.session_state.page = page
    st.rerun()

# --- AI LOGIC ---
def get_ai_analysis(items, total_cals):
    if not ai_available: return "Good food", "Walk a bit", -1
    
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
    User ate: {items} (Total Cals: {total_cals}).
    Current Health Score: {st.session_state.health_score}.
    
    Output strictly in this format:
    Review: [Short funny review]
    Recover: [Specific task like 'Take 500 steps' or 'Skip dinner']
    ScoreChange: [Integer like -5 or +2]
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        # Simple parsing (assuming AI follows format)
        review = text.split("Recover:")[0].replace("Review:", "").strip()
        recover = text.split("Recover:")[1].split("ScoreChange:")[0].strip()
        score = int(text.split("ScoreChange:")[1].strip())
        return review, recover, score
    except:
        return "You ate something!", "Drink warm water", 0

# --- PAGES ---

def show_home():
    st.title("🦁 CGC Smart-Eat")
    st.markdown("### Dashboard")

    # --- BOX 1: RECENT ORDERS ---
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        last_order = st.session_state.order_history[-1]
        c1.subheader("📦 Recent Order")
        c1.write(f"**{last_order['item']}**")
        c1.caption(f"{last_order['time']}")
        
        if c2.button("History", help="View all orders"):
            go_to("history")

    # --- BOX 2: HEALTH TRACKER ---
    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        c1.subheader("❤️ Health Tracker")
        c1.metric("Current Score", f"{st.session_state.health_score}/100")
        c1.progress(st.session_state.health_score / 100)
        
        if c2.button("Details", help="View AI Recovery Plan"):
            go_to("health")

    st.write("") # Gap
    st.write("") # Gap

    # --- BOTTOM: ORDER BUTTON ---
    if st.button("🍔 ORDER FOOD NOW", type="primary", use_container_width=True):
        go_to("order")

def show_history():
    st.title("📜 Order History")
    if st.button("⬅️ Back"): go_to("home")
    
    for order in reversed(st.session_state.order_history):
        with st.expander(f"{order['item']} ({order['time']})"):
            st.write(f"🔥 Calories: {order['cals']}")
            st.info(f"🤖 AI Said: {order['ai_msg']}")

def show_health():
    st.title("❤️ AI Health Report")
    if st.button("⬅️ Back"): go_to("home")
    
    # 1. Recovery Plan (AI Generated)
    st.success(f"💪 **Recovery Mission:**\n\n{st.session_state.recovery_plan}")
    
    # 2. Stats
    col1, col2 = st.columns(2)
    col1.metric("Today's Calories", f"{st.session_state.total_cals_today} kcal")
    col2.metric("Health Score", st.session_state.health_score)
    
    # 3. Chart
    st.subheader("Calorie Intake (Past Orders)")
    # Prepare data for chart
    df = pd.DataFrame(st.session_state.order_history)
    st.bar_chart(df, x="item", y="cals")

def show_order():
    st.title("🍽️ Menu")
    if st.button("❌ Cancel"): go_to("home")
    
    canteen = st.selectbox("Select Canteen", list(MENUS.keys()))
    
    selected_items = []
    total_cals = 0
    total_price = 0
    
    for item, cal in MENUS[canteen].items():
        price = PRICES[item]
        if st.checkbox(f"{item} - ₹{price} ({cal} cal)"):
            selected_items.append(item)
            total_cals += cal
            total_price += price
            
    if st.button(f"Pay ₹{total_price} & Analyze", type="primary", use_container_width=True):
        if not selected_items:
            st.error("Select something!")
        else:
            with st.spinner("🤖 AI Calculating Health Impact..."):
                item_str = ", ".join(selected_items)
                
                # AI Call
                rev, rec, score = get_ai_analysis(item_str, total_cals)
                
                # Update Database
                new_order = {
                    "item": item_str,
                    "cals": total_cals,
                    "time": "Just Now",
                    "ai_msg": rev
                }
                st.session_state.order_history.append(new_order)
                st.session_state.total_cals_today += total_cals
                st.session_state.health_score += score
                st.session_state.health_score = max(0, min(100, st.session_state.health_score))
                st.session_state.recovery_plan = rec
                
                st.toast("Order Placed!")
                time.sleep(1)
                go_to("home")

# --- MAIN ---
if st.session_state.page == 'home': show_home()
elif st.session_state.page == 'history': show_history()
elif st.session_state.page == 'health': show_health()
elif st.session_state.page == 'order': show_order()