import streamlit as st
from datetime import datetime

def format_date(date_val):
    """Converts raw date/timestamp to '1st Jan 2026' format."""
    if not date_val or date_val == "N/A":
        return "N/A"
    try:
        # 1. Try parsing common formats (DD-MM-YYYY or YYYY-MM-DD HH:MM:SS)
        # If it's a full timestamp from Streamlit, we split to take just the date part
        clean_date = str(date_val).split(" ")[0]
        
        # Adjusting for your specific sheet format (assuming DD-MM-YYYY)
        dt = None
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%m/%d/%Y"):
            try:
                dt = datetime.strptime(clean_date, fmt)
                break
            except:
                continue
        
        if not dt:
            return str(date_val)

        # 2. Add the ordinal suffix (st, nd, rd, th)
        day = dt.day
        if 11 <= day <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
            
        return dt.strftime(f"{day}{suffix} %b %Y")
    except:
        return str(date_val)

def show_tracking_page(ledger_sh, members_sh):
    st.title("🔍 Track My Books")
    st.write("Enter your 10-digit phone number to see your lending history.")
    
    search_phone = st.text_input("Phone Number", key="track_search_input").strip()
    
    if search_phone:
        if not search_phone.isdigit() or len(search_phone) != 10:
            st.error("⚠️ Please enter a valid 10-digit phone number.")
            return

        data = members_sh.get_all_records()
        member = next((row for row in data if str(row.get('Phone', '')).strip() == search_phone), None)

        if member:
            st.markdown(f"### Welcome {member.get('Name', 'Member')}!")
            
            c1, c2 = st.columns(2)
            lent_total = member.get('Lent count', 0)
            borrow_total = member.get('Borrowed count', 0) 
            
            with c1: 
                st.markdown(f"<div class='metric-box'>Number of times lent: <b>{lent_total}</b></div>", unsafe_allow_html=True)
            with c2: 
                st.markdown(f"<div class='metric-box'>Number of times borrowed: <b>{borrow_total}</b></div>", unsafe_allow_html=True)
            
            all_records = ledger_sh.get_all_records()
            
            my_lends = [r for r in all_records if str(r.get('Lender phone', '')).strip() == search_phone and r.get('Status') == 'Lent']
            my_borrows = [r for r in all_records if str(r.get('Borrower Phone', '')).strip() == search_phone and r.get('Status') == 'Lent']

            st.markdown("---")
            
            # 4. BOOKS LENT (Lender View)
            st.subheader("Books you've lent and are yet to receive")
            if not my_lends:
                st.info("You have no books to be collected from your borrower.")
            else:
                for row in my_lends:
                    b_title = row.get('Book Title', 'Unknown Title')
                    b_auth = row.get('Author', 'Unknown Author')
                    entry_id = row.get('ID')
                    # PULLING DATE FROM 'Date' OR 'Timestamp'
                    raw_date = row.get('Date') or row.get('Timestamp', 'N/A')
                    pretty_date = format_date(raw_date)
                    
                    with st.expander(f"📖 {b_title} - {b_auth}", expanded=True):
                        st.write(f"Lent to: **{row.get('Borrower Name', 'N/A')}** ({row.get('Borrower Phone', 'N/A')})")
                        st.write(f"Deposit: ₹{row.get('Deposit', 0)} | Date: {pretty_date}")
                        
                        btn_key = f"ret_{entry_id}" if entry_id else f"ret_fallback_{b_title}_{search_phone}"
                        if st.button(f"Mark as Returned", key=btn_key):
                            try:
                                cell = ledger_sh.find(str(entry_id))
                                ledger_sh.update_cell(cell.row, 8, "Returned")
                                st.success("Updated! Refreshing...")
                                st.rerun()
                            except:
                                st.error("Could not locate entry in sheet.")

            # 5. BOOKS BORROWED (Borrower View)
            st.subheader("Books you've borrowed and are yet to return")
            if not my_borrows:
                st.info("You have no books to be returned to your lender.")
            else:
                for row in my_borrows:
                    raw_date = row.get('Date') or row.get('Timestamp', 'N/A')
                    pretty_date = format_date(raw_date)
                    
                    st.write(f"**{row.get('Book Title', 'Unknown Title')}** by {row.get('Author', 'Unknown Author')}")
                    st.write(f"Borrowed from: {row.get('Lender Name', 'N/A')} ({row.get('Lender phone', 'N/A')})")
                    st.caption(f"Deposit Paid: ₹{row.get('Deposit', 0)} | Date: {pretty_date}")
                    st.markdown("---")

            if not my_lends and not my_borrows:
                st.write("You have no books to receive or return. Consider sharing your books if you haven't already :)")
        else:
            st.warning("Number not found. Please ensure you are registered in the ledger.")