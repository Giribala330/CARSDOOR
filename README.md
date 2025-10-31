
CARSDOOR v6 - Full Project
--------------------------

1. Edit config.py to set your MySQL password (if any).
2. Create the database & tables:
   Use your MySQL client and run:
     SOURCE schema.sql;

   Or from command line:
     "C:\wamp64\bin\mysql\mysql9.1.0\bin\mysql.exe" -u root -p < schema.sql

3. (Optional) Import predefined cars (if PRE_DATASET.json is present):
     python import_json_v6.py
   This will read PRE_DATASET.json and insert as unapproved cars (admin must approve).

4. Start the app:
     pip install -r requirements.txt
     python app.py

Admin account seeded: email=admin@carsdoor.com password=admin123

