import streamlit as st
import gspread
from datetime import datetime
import uuid
from tracker import show_tracking_page  

# --- 0. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="BTC: Book Barter", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Shared CSS for both tabs
st.markdown("""
    <style>
    input:disabled {
        -webkit-text-fill-color: #FFFFFF !important;
        color: #FFFFFF !important;
        background-color: #31333F !important;
        opacity: 1 !important;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
    }
    .metric-box {
        padding: 15px;
        border-radius: 10px;
        background-color: #262730;
        border: 1px solid #464855;
        text-align: center;
        font-size: 1.2em;
    }
    </style>
""", unsafe_allow_html=True)

# --- 1. DATABASE CONNECTION (EXCLUSIVELY FOR CLOUD) ---
try:
    # We explicitly convert the TOML secret to a Python Dictionary
    # This prevents gspread from looking for a local file
    creds_info = st.secrets["gcp_service_account"]
    creds_dict = dict(creds_info) 
    
    gc = gspread.service_account_from_dict(creds_dict)
    
    spreadsheet = gc.open("BTC: The Book Barter ledger")
    ledger_sh = spreadsheet.get_worksheet(0)
    members_sh = spreadsheet.worksheet("Members")
except Exception as e:
    st.error(f"Failed to connect to Google Sheets Cloud: {e}")
    st.stop()

# --- 2. REGISTRATION UTILITY ---
def get_member_names():
    try:
        data = members_sh.get_all_records()
        return {str(row.get('Phone', '')).strip(): str(row.get('Name', '')).strip() 
                for row in data if row.get('Phone')}
    except:
        return {}

# --- 3. MAIN NAVIGATION ---
tab_reg, tab_track = st.tabs(["📝 Register Lending", "🔍 Track My Books"])

# --- TAB 1: REGISTRATION PAGE ---
with tab_reg:
    if 'submitted' in st.session_state and st.session_state.submitted:
        st.balloons()
        st.title("You are awesome! ❤️")
        st.subheader(f"Successfully lent '{st.session_state.last_book}' to {st.session_state.last_borrower}.")
        if st.button("Register Another Lending"):
            st.session_state.submitted = False
            st.rerun()
    else:
        st.title("Lent a book?")
        st.write("Fill this form after you've handed over the book.")
        
        member_dir = get_member_names()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👤 Lender")
            l_phone = st.text_input("Your Phone", key="l_phone_reg", placeholder="10 Digits").strip()
            existing_l_name = member_dir.get(l_phone, "")
            l_name = st.text_input("Your Name", value=existing_l_name, 
                                   disabled=(existing_l_name != ""), 
                                   key=f"l_name_widget_{l_phone}")
            
        with col2:
            st.subheader("🤝 Borrower")
            b_phone = st.text_input("Borrower Phone", key="b_phone_reg", placeholder="10 Digits").strip()
            existing_b_name = member_dir.get(b_phone, "")
            b_name = st.text_input("Borrower Name", value=existing_b_name, 
                                   disabled=(existing_b_name != ""), 
                                   key=f"b_name_widget_{b_phone}")
            
            deposit = st.text_input("Deposit collected (₹)", value="0")

        st.markdown("---")
        st.subheader("📖 Book details")
        book_title = st.text_input("Book Title")
        author = st.text_input("Author Name")
        
        if st.button("Confirm Lending"):
            final_l_name = existing_l_name if existing_l_name else l_name
            final_b_name = existing_b_name if existing_b_name else b_name
            
            if all([l_phone, final_l_name, b_phone, final_b_name, book_title]):
                if len(l_phone) == 10 and len(b_phone) == 10 and (not deposit or deposit.isdigit()):
                    entry_id = str(uuid.uuid4())[:8]
                    timestamp = datetime.now().strftime("%d-%m-%Y")
                    
                    new_row = [
                        l_phone, final_l_name, b_phone, final_b_name, 
                        book_title, author, deposit if deposit else "0", "Lent", 
                        timestamp, entry_id
                    ]
                    
                    ledger_sh.append_row(new_row)
                    st.session_state.last_book = book_title
                    st.session_state.last_borrower = final_b_name
                    st.session_state.submitted = True
                    st.rerun()
                else:
                    st.error("Please ensure phone numbers are 10 digits and deposit is a number.")
            else:
                st.error("Please fill in all mandatory fields.")

# --- TAB 2: TRACKING PAGE ---
with tab_track:
    show_tracking_page(ledger_sh, members_sh)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("BTC: The Book Barter")
