import json
import mysql.connector

# --- Connect to MySQL ---
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  # leave blank if no password, else put your MySQL root password
    database="carsdoor_db"
)
cursor = db.cursor()

# --- Load the JSON file ---
with open("PRE_DATASET.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# --- Insert command ---
insert_query = """
INSERT INTO cars (
    brand, model, model_year, milage, fuel_type, engine,
    transmission, ext_col, int_col, accident, clean_title,
    price, is_approved
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
"""

count = 0
for car in data:
    try:
        cursor.execute(insert_query, (
            car.get("brand", ""),
            car.get("model", ""),
            car.get("model_year", ""),
            car.get("milage", ""),
            car.get("fuel_type", ""),
            car.get("engine", ""),
            car.get("transmission", ""),
            car.get("ext_col", ""),
            car.get("int_col", ""),
            car.get("accident", ""),
            car.get("clean_title", ""),
            car.get("price", "")
        ))
        count += 1
    except Exception as e:
        print(f"⚠️ Skipped record: {e}")

db.commit()
cursor.close()
db.close()

print(f"✅ Imported {count} predefined cars into 'cars' table successfully.")
