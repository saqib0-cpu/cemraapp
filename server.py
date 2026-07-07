from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import pyodbc

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ✅ Windows Authentication connection string for SQL Server
conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=SAQIB-PC\\SQLEXPRESS;'
    'DATABASE=ServiceBookingDB;'
    'Trusted_Connection=yes;'
)

# ✅ Load users from JSON
with open("users.json") as f:
    users = json.load(f)

# ✅ Serve the main booking page
@app.route('/')
def home():
    return send_from_directory('.', 'book.html')

# ✅ Login route
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("Username")
    password = data.get("Password")

    for user in users:
        if user["username"] == username and user["password"] == password:
            return jsonify({"message": "Login successful!"}), 200

    return jsonify({"message": "Invalid credentials"}), 401

# ✅ Book a service
@app.route('/api/orders', methods=['POST'])
def book_service():
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    services = data.get('services')
    address = data.get('address')

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Orders (name, phone, services, address) VALUES (?, ?, ?, ?)",
            (name, phone, services, address)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Booking successful!'}), 200
    except Exception as e:
        print("Error inserting booking:", e)
        return jsonify({'message': 'Database error'}), 500

# ✅ Get all bookings with full data for dashboard
@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # ✅ Full data with id and created_at
        cursor.execute("SELECT id, name, phone, services, address, created_at FROM Orders")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        orders = []
        for row in rows:
            orders.append({
                'id': row[0],
                'name': row[1],
                'phone': row[2],
                'services': row[3],
                'address': row[4],
                'created_at': str(row[5])  # ✅ Convert datetime to string
            })

        return jsonify(orders)
    except Exception as e:
        print("Fetch error:", e)
        return jsonify([])

if __name__ == '__main__':
    app.run(port=5228)
