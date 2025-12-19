import streamlit as st
import sqlite3, random, os
import qrcode
from datetime import datetime
from PIL import Image
import streamlit as st
from supabase import create_client

SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdyeGhpdGZlcXJkc3piZWlucG9nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwNDQxMTAsImV4cCI6MjA4MTYyMDExMH0.dlA3Fs_n09fwgj9LmjOr_6KtyVFKJB-Ov6PX9sB53G0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Metro + Cab Booking", layout="centered")

# ---------------- HYDERABAD METRO STATIONS ----------------
STATIONS = [
    "Miyapur","JNTU College","KPHB Colony","Kukatpally","Balanagar",
    "Moosapet","Bharat Nagar","Erragadda","ESI Hospital","SR Nagar",
    "Ameerpet","Punjagutta","Irrum Manzil","Khairatabad","Lakdi-ka-pul",
    "Assembly","Nampally","Gandhi Bhavan","Osmania Medical College",
    "MG Bus Station","Malakpet","New Market","Musarambagh",
    "Dilsukhnagar","Chaitanyapuri","Victoria Memorial",
    "LB Nagar","Nagole","Uppal","Habsiguda","Tarnaka",
    "Mettuguda","Secunderabad East","Parade Ground",
    "Paradise","Rasoolpura","Prakash Nagar","Begumpet"
]

# ---------------- QR SETUP ----------------
QR_FOLDER = "qr_codes"
os.makedirs(QR_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("metro.db")

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER,
        gender TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        from_station TEXT,
        to_station TEXT,
        time TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- FARE LOGIC ----------------
def metro_fare(frm, to):
    return max(10, abs(STATIONS.index(frm) - STATIONS.index(to)) * 5)

def cab_fare(cab_type):
    km = 5
    return 50 + km * 15 if cab_type == "Private" else 30 + km * 8

# ---------------- SESSION ----------------
if "step" not in st.session_state:
    st.session_state.step = 1

st.title("🚇 Smart Metro + 🚕 Cab Booking")

# ---------------- STEP 1: USER DETAILS ----------------
if st.session_state.step == 1:
    st.subheader("Passenger Details")

    name = st.text_input("Name")
    age = st.number_input("Age", 1, 100)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])

    if st.button("Continue"):
        if name.strip() == "":
            st.warning("Please enter name")
        else:
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (name, age, gender) VALUES (?,?,?)",
                (name, age, gender)
            )
            conn.commit()
            st.session_state.user_id = cur.lastrowid
            conn.close()
            st.session_state.step = 2
            st.rerun()

# ---------------- STEP 2: METRO BOOKING ----------------
elif st.session_state.step == 2:
    st.subheader("Metro Ticket Booking")

    frm = st.selectbox("From Station", STATIONS)
    to = st.selectbox("To Station", STATIONS)

    if st.button("Book Ticket"):
        if frm == to:
            st.warning("From and To stations must be different")
        else:
            fare = metro_fare(frm, to)
            ticket_no = f"TKT{random.randint(100000,999999)}"
            qr_path = f"{QR_FOLDER}/{ticket_no}.png"

            qrcode.make(
                f"Ticket:{ticket_no}\nFrom:{frm}\nTo:{to}\nFare:₹{fare}"
            ).save(qr_path)

            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO tickets (user_id, from_station, to_station, time)
                VALUES (?, ?, ?, ?)
            """, (
                st.session_state.user_id,
                frm,
                to,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))
            conn.commit()
            conn.close()

            st.session_state.frm = frm
            st.session_state.to = to
            st.session_state.metro_fare = fare
            st.session_state.qr = qr_path
            st.session_state.step = 3
            st.rerun()

# ---------------- STEP 3: TICKET ----------------
elif st.session_state.step == 3:
    st.subheader("🎟 Metro Ticket")

    st.write(f"Route: {st.session_state.frm} → {st.session_state.to}")
    st.write(f"💰 Metro Fare: ₹{st.session_state.metro_fare}")
    st.image(Image.open(st.session_state.qr), width=250)

    need_cab = st.radio("Need cab after metro?", ["Yes", "No"])

    if st.button("Next"):
        st.session_state.step = 4 if need_cab == "Yes" else 6
        st.rerun()

# ---------------- STEP 4: CAB BOOKING ----------------
elif st.session_state.step == 4:
    st.subheader("🚕 Cab Booking")

    dest_type = st.selectbox(
        "Destination Type",
        ["Home", "Office", "Mall", "Hospital", "Other"]
    )
    address = st.text_area("Destination Address")
    cab_type = st.selectbox("Cab Type", ["Private", "Shared"])

    if st.button("Confirm Cab"):
        if address.strip() == "":
            st.warning("Enter destination address")
        else:
            st.session_state.dest_type = dest_type
            st.session_state.address = address
            st.session_state.cab_type = cab_type
            st.session_state.cab_fare = cab_fare(cab_type)
            st.session_state.step = 5
            st.rerun()

# ---------------- STEP 5: CAB DETAILS ----------------
elif st.session_state.step == 5:
    st.subheader("🚖 Cab Details")

    models = ["Ertiga", "Swift", "Dzire", "Innova", "Alto", "Baleno"]
    colors = ["White", "Black", "Silver", "Red", "Blue"]

    st.write("📍 Destination Type:", st.session_state.dest_type)
    st.write("🏠 Address:", st.session_state.address)
    st.write("🚘 Vehicle No:", f"TS09AB{random.randint(1000,9999)}")
    st.write("🚗 Model:", random.choice(models))
    st.write("🎨 Color:", random.choice(colors))
    st.write("👨 Driver:", random.choice(["Ramesh", "Suresh", "Mahesh"]))
    st.write("📞 Phone:", f"9{random.randint(100000000,999999999)}")
    st.write("🚕 Cab Type:", st.session_state.cab_type)
    st.write("💵 Cab Fare: ₹", st.session_state.cab_fare)

    if st.session_state.cab_type == "Shared":
        st.info("👥 Co-Passengers")
        st.write("• Anil → Office")
        st.write("• Priya → Mall")

    st.success("✅ Booking completed. Safe journey!")

# ---------------- STEP 6 ----------------
elif st.session_state.step == 6:
    st.success("🎉 Metro ticket booked successfully (No cab selected)")

