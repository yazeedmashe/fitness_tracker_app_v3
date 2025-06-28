import streamlit as st
import pandas as pd
import sqlite3
import hashlib

DB_PATH = r"Database/FT_DB.db"

# Initialize DB (runs only once)
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        # Assume exercises and gym_log tables already exist
        conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()

def authenticate_user(username, password):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (username, hash_password(password))
        )
        result = cursor.fetchone()
        if result:
            return result[0]  # Return user id
        else:
            return None

# Initialize DB
init_db()

# Session setup
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    menu = st.radio("Choose Option", ['Login', 'Sign Up'])

    if menu == "Sign Up":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            if not new_user or not new_pass:
                st.error("Please enter both username and password.")
            else:
                try:
                    add_user(new_user, new_pass)
                    st.success("Account created! Please login.")
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")

    elif menu == "Login":
        st.subheader("Login")
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user_id = authenticate_user(user, password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.user_id = user_id
                st.success(f"Welcome, {user}!")
                st.rerun()
            else:
                st.error("Invalid credentials.")

else:
    st.title(f"{st.session_state.user}'s Dashboard")
    st.write("This is your gym progress tracker, personalized for you!")

    st.sidebar.title("Gym Session Logger")
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM exercises", conn)

    exercise_names = st.sidebar.multiselect("Select exercise:", df['name'].unique())
    total_weight = st.sidebar.text_input("Total Weight Moved (Kg):")
    total_reps = st.sidebar.text_input("Total Repetitions Performed:")
    submit = st.sidebar.button("Submit")
    logout = st.sidebar.button("Logout")

    if submit:
        exer_row = df[df["name"].isin(exercise_names)]
        if exer_row.empty:
            st.error("Selected exercise not found.")
        else:
            exer_id = int(exer_row['id'].values[0])
            user_id = st.session_state.user_id
            if not total_weight.isdigit() or not total_reps.isdigit():
                st.error("Please enter numeric values for weight and reps.")
            else:
                with sqlite3.connect(DB_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO gym_log (userid, exercise_id, total_weight, total_reps, session_date) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                        (user_id, exer_id, int(total_weight), int(total_reps))
                    )
                    conn.commit()
                st.success("Log saved successfully.")

    if logout:
        st.session_state.logged_in = False
        st.rerun()

    user_id = st.session_state.user_id
    with sqlite3.connect(DB_PATH) as conn:
        total_weight_df = pd.read_sql("SELECT SUM(total_weight) AS total_weight FROM gym_log WHERE userid = ?", conn, params=(user_id,))
        total_reps_df = pd.read_sql("SELECT SUM(total_reps) AS total_reps FROM gym_log WHERE userid = ?", conn, params=(user_id,))
        exer_count_df = pd.read_sql("SELECT COUNT(*) AS rep_count FROM gym_log WHERE userid = ?", conn, params=(user_id,))

    st.markdown("Key Insights From Your Gym Sessions:")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Weight Moved", int(total_weight_df.iloc[0, 0] or 0))
    col2.metric("Total Reps Performed", int(total_reps_df.iloc[0, 0] or 0))
    col3.metric("Exercises Logged", int(exer_count_df.iloc[0, 0] or 0))

    st.markdown("---")

    with sqlite3.connect(DB_PATH) as conn:
        weight_over_time = pd.read_sql(
            "SELECT DATE(session_date) AS date, SUM(total_weight) AS total_weight FROM gym_log WHERE userid = ? GROUP BY DATE(session_date)",
            conn, params=(user_id,)
        )
    st.markdown("Your Progress Over Time")
    st.line_chart(weight_over_time.set_index('date')['total_weight'])

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)

    with sqlite3.connect(DB_PATH) as conn:
        exer_dist = pd.read_sql(
            "SELECT e.name, COUNT(*) AS count FROM gym_log g INNER JOIN exercises e ON g.exercise_id = e.id WHERE userid = ? GROUP BY e.name ORDER BY count DESC",
            conn, params=(user_id,)
        )
    with col_chart1:
        st.markdown("Your Exercise Distribution:")
        st.bar_chart(exer_dist.set_index('name')['count'].sort_values(ascending=False))

    with sqlite3.connect(DB_PATH) as conn:
        extype_dist = pd.read_sql(
            "SELECT e.type AS type, COUNT(*) AS count FROM gym_log g INNER JOIN exercises e ON g.exercise_id = e.id WHERE userid = ? GROUP BY e.type ORDER BY count DESC",
            conn, params=(user_id,)
        )
    with col_chart2:
        st.markdown("Breakdown by Exercise Type:")
        st.bar_chart(extype_dist.set_index('type')['count'])

    st.markdown("---")

    with sqlite3.connect(DB_PATH) as conn:
        records = pd.read_sql(
            """
            SELECT e.name AS exercise_name, MAX(total_weight) AS best_weight
            FROM gym_log g
            INNER JOIN exercises e ON g.exercise_id = e.id
            WHERE userid = ?
            GROUP BY exercise_name
            """,
            conn, params=(user_id,)
        )
    st.markdown("Your Personal Best:")
    st.dataframe(records.sort_values(by='best_weight', ascending=False))
