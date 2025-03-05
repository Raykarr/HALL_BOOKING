import streamlit as st
import pandas as pd
import datetime
import hashlib
import os
import json
from datetime import datetime, timedelta
import calendar

# Set page configuration
st.set_page_config(page_title="Hall Booking System", layout="wide")

# File paths
MASTER_FILE = r"D:\\Downloads\\master_data.xlsx"
BOOKINGS_FILE = "bookings.json"
PENDING_FILE = "pending_bookings.json"

# Custom CSS to improve UI
st.markdown("""
<style>
    .calendar-day {
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 8px;
        min-height: 100px;
        background-color: #f9f9f9;
        margin: 2px;
    }
    .calendar-day:hover {
        background-color: #f0f0f0;
    }
    .calendar-day-header {
        font-weight: bold;
        text-align: center;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 5px;
        margin-bottom: 5px;
    }
    .booking-slot {
        background-color: #ffebee;
        padding: 5px;
        border-radius: 5px;
        margin-bottom: 5px;
        border-left: 4px solid #f44336;
        font-size: 0.9em;
    }
    .available-text {
        color: #2e7d32;
        font-weight: bold;
        text-align: center;
        margin-top: 30px;
        background-color: #e8f5e9;
        padding: 8px;
        border-radius: 4px;
    }
    .unavailable-text {
        color: #757575;
        text-align: center;
        margin-top: 30px;
        background-color: #f5f5f5;
        padding: 8px;
        border-radius: 4px;
    }
    .stButton button {
        width: 100%;
    }
    .booking-form {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    .divider {
        height: 1px;
        background-color: #e0e0e0;
        margin: 20px 0;
    }
    .custom-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: white;
    }
    .past-date {
        opacity: 0.5;
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables if they don't exist
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'is_hr' not in st.session_state:
    st.session_state.is_hr = False
if 'show_notification' not in st.session_state:
    st.session_state.show_notification = False
if 'notification_message' not in st.session_state:
    st.session_state.notification_message = ""
# New session state variables for persistent form data
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()
if 'selected_start_time' not in st.session_state:
    st.session_state.selected_start_time = datetime.now().time()
if 'selected_end_time' not in st.session_state:
    st.session_state.selected_end_time = (datetime.combine(datetime.today(), datetime.now().time()) + timedelta(hours=1)).time()
if 'booking_purpose' not in st.session_state:
    st.session_state.booking_purpose = ""
if 'availability_checked' not in st.session_state:
    st.session_state.availability_checked = False
if 'is_available' not in st.session_state:
    st.session_state.is_available = False
if 'current_view_month' not in st.session_state:
    st.session_state.current_view_month = datetime.now().month
if 'current_view_year' not in st.session_state:
    st.session_state.current_view_year = datetime.now().year

# Function to load master data
@st.cache_data
def load_master_data():
    if os.path.exists(MASTER_FILE):
        df = pd.read_excel(MASTER_FILE)
        return df
    else:
        st.error(f"Master file {MASTER_FILE} not found!")
        return pd.DataFrame(columns=["Employee_ID", "Employee_Name", "Password", "Role"])

# Function to load bookings
def load_bookings():
    if os.path.exists(BOOKINGS_FILE):
        with open(BOOKINGS_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    else:
        return []

# Function to load pending bookings
def load_pending_bookings():
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []
    else:
        return []

# Function to save bookings
def save_bookings(bookings):
    with open(BOOKINGS_FILE, 'w') as file:
        json.dump(bookings, file)

# Function to save pending bookings
def save_pending_bookings(pending_bookings):
    with open(PENDING_FILE, 'w') as file:
        json.dump(pending_bookings, file)

# Function to check if a time slot is available
def is_slot_available(start_datetime, end_datetime, bookings):
    for booking in bookings:
        booking_start = datetime.strptime(booking['start_datetime'], "%Y-%m-%d %H:%M")
        booking_end = datetime.strptime(booking['end_datetime'], "%Y-%m-%d %H:%M")
        
        # Check if there's an overlap
        if (start_datetime < booking_end and end_datetime > booking_start):
            return False
    return True

# Function to hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to verify login
def verify_login(employee_id, password, master_data):
    if master_data.empty:
        return False, "", False
        
    # Convert employee_id to the appropriate type if necessary
    if master_data['Employee_ID'].dtype == 'int64':
        employee_id = int(employee_id)
    
    user = master_data[master_data['Employee_ID'] == employee_id]
    
    if not user.empty:
        stored_password = user['Password'].values[0]
        is_hr = user['Role'].values[0].upper() == 'HR' if 'Role' in user.columns else False
        user_name = user['Employee_Name'].values[0]
        
        # If passwords are stored as hashes in the Excel file
        # return stored_password == hash_password(password), user_name, is_hr
        
        # If passwords are stored in plain text in the Excel file (not recommended for production)
        return stored_password == password, user_name, is_hr
    return False, "", False

# Function to handle logout
def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.is_hr = False

# Function to update session state for date/time selection
def update_date_selection(date):
    st.session_state.selected_date = date
    st.session_state.availability_checked = False

def update_start_time(time):
    st.session_state.selected_start_time = time
    st.session_state.availability_checked = False

def update_end_time(time):
    st.session_state.selected_end_time = time
    st.session_state.availability_checked = False

def update_purpose(purpose):
    st.session_state.booking_purpose = purpose

def check_availability():
    start_datetime = datetime.combine(st.session_state.selected_date, st.session_state.selected_start_time)
    end_datetime = datetime.combine(st.session_state.selected_date, st.session_state.selected_end_time)
    
    # Validate inputs
    if start_datetime < datetime.now():
        st.error("Cannot book in the past!")
        st.session_state.availability_checked = False
        st.session_state.is_available = False
        return
    elif end_datetime <= start_datetime:
        st.error("End time must be after start time!")
        st.session_state.availability_checked = False
        st.session_state.is_available = False
        return
    
    bookings = load_bookings()
    is_available = is_slot_available(start_datetime, end_datetime, bookings)
    
    st.session_state.availability_checked = True
    st.session_state.is_available = is_available

def book_hall():
    if not st.session_state.is_available:
        st.error("Please check availability first and ensure the slot is available.")
        return
    
    start_datetime = datetime.combine(st.session_state.selected_date, st.session_state.selected_start_time)
    end_datetime = datetime.combine(st.session_state.selected_date, st.session_state.selected_end_time)
    
    # Create booking object
    new_booking = {
        'user_id': st.session_state.user_id,
        'booked_by': st.session_state.user_name,
        'start_datetime': start_datetime.strftime("%Y-%m-%d %H:%M"),
        'end_datetime': end_datetime.strftime("%Y-%m-%d %H:%M"),
        'purpose': st.session_state.booking_purpose,
        'status': 'pending'
    }
    
    # If HR is booking, auto-approve
    if st.session_state.is_hr:
        new_booking['status'] = 'approved'
        bookings = load_bookings()
        bookings.append(new_booking)
        save_bookings(bookings)
        st.success("Hall booked successfully!")
    else:
        # Add to pending bookings
        pending_bookings = load_pending_bookings()
        pending_bookings.append(new_booking)
        save_pending_bookings(pending_bookings)
        st.success("Booking request submitted and pending HR approval!")
    
    # Reset form
    st.session_state.booking_purpose = ""
    st.session_state.availability_checked = False
    st.session_state.is_available = False

# Calendar navigation functions
def prev_month():
    if st.session_state.current_view_month == 1:
        st.session_state.current_view_month = 12
        st.session_state.current_view_year -= 1
    else:
        st.session_state.current_view_month -= 1
    st.rerun()  # Force page refresh to update calendar

def next_month():
    if st.session_state.current_view_month == 12:
        st.session_state.current_view_month = 1
        st.session_state.current_view_year += 1
    else:
        st.session_state.current_view_month += 1
    st.rerun()  # Force page refresh to update calendar

# Function to display improved calendar with bookings
def display_calendar(bookings):
    st.subheader("Hall Booking Calendar")
    
    # Calendar navigation
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("← Previous Month"):
            prev_month()
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>{calendar.month_name[st.session_state.current_view_month]} {st.session_state.current_view_year}</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("Next Month →"):
            next_month()
    
    # Get first day of month and number of days in month
    first_day = datetime(st.session_state.current_view_year, st.session_state.current_view_month, 1)
    days_in_month = calendar.monthrange(st.session_state.current_view_year, st.session_state.current_view_month)[1]
    
    # Get the weekday of the first day (0 is Monday in calendar module)
    first_weekday = calendar.monthrange(st.session_state.current_view_year, st.session_state.current_view_month)[0]
    
    # Create calendar grid
    # Display day names (header row)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols = st.columns(7)
    for i, day_name in enumerate(day_names):
        with cols[i]:
            st.markdown(f"<div style='text-align:center; font-weight:bold;'>{day_name}</div>", unsafe_allow_html=True)
    
    # Calculate total number of cells needed (previous month days + current month days)
    total_cells = first_weekday + days_in_month
    weeks = (total_cells + 6) // 7  # Round up to complete weeks
    
    # Current date for comparison
    current_date = datetime.now().date()
    
    # Display the calendar cells
    day_counter = 1
    for week in range(weeks):
        cols = st.columns(7)
        for weekday in range(7):
            with cols[weekday]:
                if (week == 0 and weekday < first_weekday) or (day_counter > days_in_month):
                    # Empty cell
                    st.markdown("<div class='calendar-day' style='opacity:0.3;'></div>", unsafe_allow_html=True)
                else:
                    # Valid day cell
                    date_obj = datetime(st.session_state.current_view_year, st.session_state.current_view_month, day_counter).date()
                    is_today = date_obj == current_date
                    is_selected = date_obj == st.session_state.selected_date
                    is_past_date = date_obj < current_date
                    
                    # Find bookings for this date
                    date_str = date_obj.strftime("%Y-%m-%d")
                    day_bookings = [b for b in bookings if date_str in b['start_datetime']]
                    
                    # Determine cell style
                    cell_style = "calendar-day"
                    if is_today:
                        cell_style += " border-primary"
                    if is_selected:
                        cell_style += " bg-light"
                    if is_past_date:
                        cell_style += " past-date"
                    
                    # Day cell content
                    st.markdown(
                        f"""
                        <div class='{cell_style}'>
                            <div class='calendar-day-header'>
                                {day_counter}{" (Today)" if is_today else ""}
                            </div>
                        """
                        + (
                            "".join([
                                f"""
                                <div class='booking-slot'>
                                    {datetime.strptime(booking['start_datetime'], "%Y-%m-%d %H:%M").strftime("%H:%M")} - 
                                    {datetime.strptime(booking['end_datetime'], "%Y-%m-%d %H:%M").strftime("%H:%M")}
                                    <br>{booking['booked_by']}
                                </div>
                                """
                                for booking in day_bookings
                            ])
                            if day_bookings
                            else (
                                "<div class='unavailable-text'>Past Date</div>" 
                                if is_past_date 
                                else "<div class='available-text'>Available</div>"
                            )
                        )
                        + "</div>",
                        unsafe_allow_html=True,
                    )
                    
                    # Add a button to select this date with formatted date
                    formatted_date = date_obj.strftime("%d-%m-%Y")
                    if st.button(f"Select {formatted_date}", key=f"select_day_{date_obj}", disabled=is_past_date):
                        update_date_selection(date_obj)
                    
                    day_counter += 1

# Function to display user's bookings
def display_user_bookings(user_id, bookings):
    st.subheader("Your Bookings")
    
    user_bookings = [b for b in bookings if b['user_id'] == user_id]
    
    if not user_bookings:
        st.info("You have no active bookings.")
        return
    
    for i, booking in enumerate(user_bookings):
        start_datetime = datetime.strptime(booking['start_datetime'], "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(booking['end_datetime'], "%Y-%m-%d %H:%M")
        
        st.markdown(f"<div class='custom-card'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 3, 1])
        with col1:
            st.write(f"📅 **Date:** {start_datetime.strftime('%d-%m-%Y')}")
            st.write(f"⏰ **Time:** {start_datetime.strftime('%H:%M')} - {end_datetime.strftime('%H:%M')}")
        with col2:
            st.write(f"📝 **Purpose:** {booking.get('purpose', 'N/A')}")
            st.write(f"👤 **Booked by:** {booking['booked_by']}")
        with col3:
            if st.button("Cancel", key=f"cancel_{i}"):
                bookings.remove(booking)
                save_bookings(bookings)
                st.success("Booking cancelled successfully!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Function to display pending notifications for the user
def display_notifications(user_id, pending_bookings, bookings):
    user_notifications = [b for b in pending_bookings if b['user_id'] == user_id and b.get('status_updated', False)]
    
    if not user_notifications:
        return
    
    for notification in user_notifications:
        # Convert date format for display
        start_datetime = datetime.strptime(notification['start_datetime'], "%Y-%m-%d %H:%M")
        formatted_date = start_datetime.strftime("%d-%m-%Y %H:%M")
        
        if notification['status'] == 'approved':
            st.success(f"Your booking request for {formatted_date} has been approved!")
        else:
            st.error(f"Your booking request for {formatted_date} has been denied!")
        
        # Remove the notification after showing it
        pending_bookings.remove(notification)
    
    save_pending_bookings(pending_bookings)

# Function to display HR approval section
def display_hr_section(pending_bookings, bookings):
    st.subheader("HR Approval Section")
    
    pending_requests = [b for b in pending_bookings if not b.get('status_updated', False)]
    
    if not pending_requests:
        st.info("No pending requests.")
        return
    
    for i, request in enumerate(pending_requests):
        start_datetime = datetime.strptime(request['start_datetime'], "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(request['end_datetime'], "%Y-%m-%d %H:%M")
        
        st.markdown(f"<div class='custom-card'>", unsafe_allow_html=True)
        st.write(f"**Request #{i+1}**")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"👤 **Employee:** {request['booked_by']}")
            st.write(f"📅 **Date:** {start_datetime.strftime('%d-%m-%Y')}")
            st.write(f"⏰ **Time:** {start_datetime.strftime('%H:%M')} - {end_datetime.strftime('%H:%M')}")
        with col2:
            st.write(f"📝 **Purpose:** {request.get('purpose', 'N/A')}")
            
            col_approve, col_deny = st.columns(2)
            with col_approve:
                if st.button("Approve", key=f"approve_{i}"):
                    # Mark as approved
                    request['status'] = 'approved'
                    request['status_updated'] = True
                    
                    # Add to confirmed bookings
                    bookings.append(request.copy())
                    
                    # Save changes
                    save_bookings(bookings)
                    save_pending_bookings(pending_bookings)
                    
                    st.success("Request approved!")
                    st.rerun()
            
            with col_deny:
                if st.button("Deny", key=f"deny_{i}"):
                    # Mark as denied
                    request['status'] = 'denied'
                    request['status_updated'] = True
                    
                    # Save changes
                    save_pending_bookings(pending_bookings)
                    
                    st.error("Request denied!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Function to display HR manage bookings section
def display_hr_manage_bookings(bookings):
    st.subheader("Manage Existing Bookings")
    
    if not bookings:
        st.info("No active bookings.")
        return
    
    for i, booking in enumerate(bookings):
        start_datetime = datetime.strptime(booking['start_datetime'], "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(booking['end_datetime'], "%Y-%m-%d %H:%M")
        
        st.markdown(f"<div class='custom-card'>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([3, 3, 1])
        with col1:
            st.write(f"📅 **Date:** {start_datetime.strftime('%Y-%m-%d')}")
            st.write(f"⏰ **Time:** {start_datetime.strftime('%H:%M')} - {end_datetime.strftime('%H:%M')}")
        with col2:
            st.write(f"📝 **Purpose:** {booking.get('purpose', 'N/A')}")
            st.write(f"👤 **Booked by:** {booking['booked_by']}")
        with col3:
            if st.button("Cancel", key=f"hr_cancel_{i}"):
                bookings.remove(booking)
                save_bookings(bookings)
                st.success("Booking cancelled successfully!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Main application
def main():
    st.title("Hall Booking System")
    
    # Load data
    master_data = load_master_data()
    bookings = load_bookings()
    pending_bookings = load_pending_bookings()
    
    # Sidebar for login
    with st.sidebar:
        st.header("User Panel")
        
        if not st.session_state.logged_in:
            st.subheader("Login")
            employee_id = st.text_input("Employee ID")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                if employee_id and password:
                    is_valid, user_name, is_hr = verify_login(employee_id, password, master_data)
                    
                    if is_valid:
                        st.session_state.logged_in = True
                        st.session_state.user_id = employee_id
                        st.session_state.user_name = user_name
                        st.session_state.is_hr = is_hr
                        st.success(f"Welcome, {user_name}!")
                        st.rerun()
                    else:
                        st.error("Invalid Employee ID or Password!")
                else:
                    st.warning("Please enter both Employee ID and Password!")
        else:
            st.write(f"Logged in as: **{st.session_state.user_name}**")
            st.write(f"Role: **{'HR' if st.session_state.is_hr else 'Employee'}**")
            
            if st.button("Logout"):
                logout()
                st.success("Logged out successfully!")
                st.rerun()
    
    # Main content
    if st.session_state.logged_in:
        # Display notifications
        display_notifications(st.session_state.user_id, pending_bookings, bookings)
        
        # Display calendar with bookings
        display_calendar(bookings)
        
        # Display user's bookings
        display_user_bookings(st.session_state.user_id, bookings)
        
        # Book a hall section
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.header("Book the Hall")
        
        # Booking form with improved layout
        st.markdown("<div class='booking-form'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Update session state directly when the date input changes
            new_date = st.date_input(
                "Select Date", 
                value=st.session_state.selected_date,
                min_value=datetime.now().date(),
            )
            # Only update if changed to avoid infinite loops
            if new_date != st.session_state.selected_date:
                st.session_state.selected_date = new_date
                st.session_state.availability_checked = False
        
        with col2:
            st.write("Select Time")
            start_time_col, end_time_col = st.columns(2)
            
            with start_time_col:
                # Update session state directly when the time input changes
                new_start_time = st.time_input(
                    "Start Time", 
                    value=st.session_state.selected_start_time,
                )
                # Only update if changed to avoid infinite loops
                if new_start_time != st.session_state.selected_start_time:
                    st.session_state.selected_start_time = new_start_time
                    st.session_state.availability_checked = False
            
            with end_time_col:
                # Update session state directly when the time input changes
                new_end_time = st.time_input(
                    "End Time", 
                    value=st.session_state.selected_end_time,
                )
                # Only update if changed to avoid infinite loops
                if new_end_time != st.session_state.selected_end_time:
                    st.session_state.selected_end_time = new_end_time
                    st.session_state.availability_checked = False
        
        # Update session state directly when the purpose input changes
        new_purpose = st.text_area(
            "Purpose of Booking", 
            value=st.session_state.booking_purpose,
        )
        # Only update if changed to avoid infinite loops
        if new_purpose != st.session_state.booking_purpose:
            st.session_state.booking_purpose = new_purpose
        
        # Separate availability check and booking
        col_check, col_book = st.columns(2)
        
        with col_check:
            if st.button("Check Availability"):
                check_availability()
        
        with col_book:
            if st.button("Book Hall", disabled=not st.session_state.availability_checked or not st.session_state.is_available):
                book_hall()
                
        # Display availability status
        if st.session_state.availability_checked:
            if st.session_state.is_available:
                st.success("This time slot is available! You can proceed with booking.")
            else:
                st.error("Sorry, this time slot is already booked. Please select another time.")
                
        st.markdown("</div>", unsafe_allow_html=True)
        
        # HR specific sections
        if st.session_state.is_hr:
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            display_hr_section(pending_bookings, bookings)
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            display_hr_manage_bookings(bookings)
    else:
        st.info("Please login to use the Hall Booking System.")

if __name__ == "__main__":
    main()