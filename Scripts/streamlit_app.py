import streamlit as st
import pandas as pd
import sqlite3
import hashlib

# Connect to your main app DB
db = sqlite3.connect(r"Database\FT_DB.db")

# One-time user DB init
def init_db():
    conn = db
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    conn = db
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                   (username, hash_password(password)))
    conn.commit()

def authenticate_user(username, password):
    conn = db
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                   (username, hash_password(password)))
    result = cursor.fetchone()
    return result is not None

def get_user_id(username):
    conn = db
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    return result[0] if result else None


# Initialize DB (runs only once)
init_db()

# Session setup
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# If NOT logged in, show login/signup
if not st.session_state.logged_in:
    menu = st.radio("Choose Option", ['Login', 'Sign Up'])

    if menu == "Sign Up":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            try:
                add_user(new_user, new_pass)
                st.success("Account created! Please login.")
            except sqlite3.IntegrityError:
                st.error("Username already exists")

    elif menu == "Login":
        st.subheader("Login")
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate_user(user, password):
                st.session_state.logged_in = True
                st.session_state.user = user
                st.success(f"Welcome, {user}!")
                st.rerun()
            else:
                st.error("Invalid credentials")

# If logged in, show dashboard
else:
    st.title(f"{st.session_state.user}'s Dashboard")
    st.write("This is your gym progress tracker, personalized for you!")
    st.sidebar.title("Gym Session Logger")
    # fetching excersice list
    df = pd.read_sql("SELECT * FROM exercises",db)
    excersice_name = st.sidebar.multiselect("Select excersice:",df['name'].unique())
    total_weight = st.sidebar.text_input("Total Weight Moved (Kg) :")
    total_reps = st.sidebar.text_input("Total Repetitions Performed :")
    submit = st.sidebar.button("Submit")
    if submit:
        exer_row = df[df["name"].isin(excersice_name)]
        if not exer_row.empty:
            exer_id = int(exer_row['id'].values[0])
            user_id = get_user_id(st.session_state.user)
            if user_id is None:
                st.error("User Not Found in DB")
            elif not total_weight.isdigit() or not total_reps.isdigit():
                st.error("Please Enter Numeric Values for weight and reps")
            else:
                conn = db
                cursor = db.cursor()
                cursor.execute("INSERT INTO gym_log (userid,exercise_id,total_weight,total_reps,session_date) VALUES (?,?,?,?,CURRENT_TIMESTAMP)",(user_id,exer_id,int(total_weight),int(total_reps)))
                conn.commit()
                st.success("Log Saved Succesfully")
        else:
            st.error("Selected Exercise Not Found")
    
    total_weight = pd.read_sql("SELECT sum(total_weight) from gym_log WHERE userid = ?",db,params=(get_user_id(st.session_state.user),))
    total_reps = pd.read_sql('SELECT sum(total_reps) from gym_log WHERE userid = ?',db,params=(get_user_id(st.session_state.user),))
    exer_count = pd.read_sql("SELECT count( * ) AS rep_count FROM gym_log WHERE userid = ?",db,params=(get_user_id(st.session_state.user),))

    st.markdown("Key Insights From your Gym Sessions :")
    col1,col2,col3 = st.columns(3)
    col1.metric("Total Weight Moved", int(total_weight.iloc[0, 0] or 0))
    col2.metric("Total Reps Performed", int(total_reps.iloc[0, 0] or 0))
    col3.metric("Exercises Logged", int(exer_count.iloc[0, 0] or 0))

    st.markdown("---")

    weight_over_time = pd.read_sql("select date(session_date) as date, sum(total_weight) as total_weight from gym_log WHERE userid = ? GROUP BY DATE(session_date)",db,params=(get_user_id(st.session_state.user),))

    st.markdown("Your Progress Over Time")

    st.line_chart(weight_over_time.set_index('date')['total_weight'])

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("Your Exercise Distribution :")
        exer_dist = pd.read_sql("select e.name, count(*) as count from gym_log g inner join exercises e on g.exercise_id = e.id where userid = ? group by e.name order by count(*) DESC",db,params=(get_user_id(st.session_state.user),))
        st.bar_chart(exer_dist.set_index('name')['count'].sort_values(ascending=False))
    
    with col_chart2:
        st.markdown("Breakdown by exercise type :")
        extype_dist = pd.read_sql("select e.type as type, count(*) as count from gym_log g inner join exercises e on g.exercise_id = e.id where userid = ? group by e.type order by count(*) DESC",db,params=(get_user_id(st.session_state.user),))
        st.bar_chart(extype_dist.set_index('type')['count'])

    st.markdown("---")

    st.markdown("Your Personal Best :")

    records = pd.read_sql("""SELECT e.name as exercise_name, MAX(total_weight) as best_weight FROM gym_log inner join exercises e on gym_log.exercise_id = e.id WHERE userid = ? GROUP BY exercise_name""", db, params=(get_user_id(st.session_state.user),))
    st.dataframe(records.sort_values(by='best_weight',ascending=False))


    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
