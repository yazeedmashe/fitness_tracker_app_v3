# 🏋️ Gym Progress Tracker

A lightweight and secure web app built with **Streamlit** and **SQLite** to help users track their gym workouts, analyze progress, and visualize exercise data over time.

---

## 🚀 Features

- **User Authentication**
  - Secure login and sign-up system with password hashing using SHA-256.
  
- **Exercise Logging**
  - Select exercises from a predefined list.
  - Enter total weight moved and total repetitions performed.
  - Logs are timestamped and stored per user.

- **Personalized Dashboard**
  - Key metrics: Total weight, reps, and exercises logged.
  - Line chart showing weight lifted over time.
  - Bar charts for exercise distribution and type breakdown.
  - Personal best records for each exercise.

---

## 📦 Project Structure

├── app.py # Main Streamlit app
├── Database/
│ └── FT_DB.db # SQLite database file
├── requirements.txt # Dependencies
└── README.md # Project documentation

Create and Activate Virtual Environment

bash
Copy
Edit
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install Dependencies

bash
Copy
Edit
pip install -r requirements.txt
Run the App

bash
Copy
Edit
streamlit run app.py
🧩 Database Schema
users Table
Field	Type	Description
username	TEXT	Primary Key
password	TEXT	Hashed user password

exercises Table
Must be pre-populated with exercise records (id, name, type)

gym_log Table
Field	Type	Description
userid	INTEGER	Foreign key to users table
exercise_id	INTEGER	Foreign key to exercises table
total_weight	INTEGER	Total weight moved (kg)
total_reps	INTEGER	Total repetitions
session_date	TIMESTAMP	Time of entry

🛡️ Security
Passwords are hashed using SHA-256.

SQL queries use parameterized statements to prevent SQL injection.

Session state managed by Streamlit to maintain user login status.

📊 Visualizations
Line Chart: Weight lifted over time

Bar Charts: Frequency by exercise and type

Table: Personal best weights per exercise

📌 TODO
Add password reset functionality

Admin panel for exercise management

Export logs to CSV

Mobile UI optimization
