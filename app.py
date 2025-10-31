
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector, os, json
from werkzeug.security import generate_password_hash, check_password_hash
from config import DB_CONFIG, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY
DATA_FILE = os.path.join(os.path.dirname(__file__), 'PRE_DATASET.json')

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def get_user_by_email(email):
    cnx = get_db(); cur = cnx.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    u = cur.fetchone(); cur.close(); cnx.close()
    return u

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']; name = request.form['name']; email = request.form['email']; password = request.form['password']
        address = request.form.get('address',''); phone = request.form.get('phone','')
        if get_user_by_email(email):
            flash('Email already registered','danger'); return redirect(url_for('register'))
        pwd = generate_password_hash(password)
        cnx = get_db(); cur = cnx.cursor()
        cur.execute("INSERT INTO users (role,name,email,password_hash,address,phone,is_approved) VALUES (%s,%s,%s,%s,%s,%s,0)", (role,name,email,pwd,address,phone))
        cnx.commit(); cur.close(); cnx.close()
        flash('Registration request submitted. Await admin approval.','success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']; password = request.form['password']
        user = get_user_by_email(email)
        if not user:
            flash('Invalid credentials','danger'); return redirect(url_for('login'))
        if not user['is_approved'] and user['role']!='admin':
            flash('Your account is awaiting admin approval.','warning'); return redirect(url_for('login'))
        if check_password_hash(user['password_hash'], password):
            session['user_id']=user['id']; session['role']=user['role']; session['name']=user['name']
            return redirect(url_for(session['role'] + '_dashboard'))
        flash('Invalid credentials','danger'); return redirect(url_for('login'))
    # optional preselect role
    as_role = request.args.get('as')
    return render_template('login.html', as_role=as_role)

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('index'))

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if session.get('role')!='admin': return redirect(url_for('login'))
    cnx=get_db(); cur=cnx.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE is_approved=0 AND role IN ('buyer','seller')"); pending_users=cur.fetchall()
    cur.execute("SELECT c.*, u.name as seller_name FROM cars c LEFT JOIN users u ON c.seller_id=u.id WHERE c.is_approved=0"); pending_cars=cur.fetchall()
    cur.execute("SELECT o.*, c.brand, c.model FROM orders o JOIN cars c ON o.car_id=c.id WHERE o.status='pending'"); pending_orders=cur.fetchall()
    cur.execute("SELECT id,name,email FROM users WHERE role='seller' AND is_approved=1"); sellers=cur.fetchall()
    cur.execute("SELECT DISTINCT brand FROM cars WHERE brand IS NOT NULL AND brand<>''"); brands_db=[r['brand'] for r in cur.fetchall()]
    try:
        with open(DATA_FILE,'r',encoding='utf-8') as f: j=json.load(f); brands_json=sorted({(c.get('brand') or '').strip() for c in j if c.get('brand')})
    except: brands_json=[]
    brands=sorted(set(brands_db+brands_json))
    cur.close(); cnx.close()
    return render_template('admin_dashboard.html', pending_users=pending_users, pending_cars=pending_cars, pending_orders=pending_orders, sellers=sellers, brands=brands)

@app.route('/admin/approve_user/<int:user_id>')
def approve_user(user_id):
    if session.get('role')!='admin': return redirect(url_for('login'))
    cnx=get_db(); cur=cnx.cursor(); cur.execute("UPDATE users SET is_approved=1 WHERE id=%s",(user_id,)); cnx.commit(); cur.close(); cnx.close()
    flash('User approved','success'); return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve_car/<int:car_id>', methods=['POST'])
def approve_car(car_id):
    if session.get('role')!='admin': return redirect(url_for('login'))
    seller_id = request.form.get('seller_id') or None
    cnx=get_db(); cur=cnx.cursor()
    if seller_id:
        cur.execute("UPDATE cars SET seller_id=%s, is_approved=1 WHERE id=%s",(seller_id, car_id))
    else:
        cur.execute("UPDATE cars SET is_approved=1 WHERE id=%s",(car_id,))
    cnx.commit(); cur.close(); cnx.close()
    flash('Car approved and assigned','success'); return redirect(url_for('admin_dashboard'))

@app.route('/admin/order_action/<int:order_id>', methods=['POST'])
def admin_order_action(order_id):
    if session.get('role')!='admin': return redirect(url_for('login'))
    action = request.form.get('action')
    cnx=get_db(); cur=cnx.cursor()
    if action=='confirm':
        cur.execute("UPDATE orders SET status='confirmed' WHERE id=%s",(order_id,))
    else:
        cur.execute("UPDATE orders SET status='cancelled' WHERE id=%s",(order_id,))
    cnx.commit(); cur.close(); cnx.close()
    flash('Order updated','success'); return redirect(url_for('admin_dashboard'))

# Seller dashboard
@app.route('/seller')
def seller_dashboard():
    if session.get('role')!='seller': return redirect(url_for('login'))
    uid=session['user_id']; brand_filter=request.args.get('brand'); year_filter=request.args.get('year')
    cnx=get_db(); cur=cnx.cursor(dictionary=True)
    sql="SELECT * FROM cars WHERE seller_id=%s"; params=[uid]
    if brand_filter: sql += " AND brand=%s"; params.append(brand_filter)
    if year_filter: sql += " AND model_year=%s"; params.append(year_filter)
    cur.execute(sql, tuple(params)); mycars=cur.fetchall()
    cur.execute("SELECT o.*, u.name as buyer_name, u.phone as buyer_phone, c.brand, c.model FROM orders o JOIN users u ON o.buyer_id=u.id JOIN cars c ON o.car_id=c.id WHERE o.seller_id=%s",(uid,))
    orders=cur.fetchall()
    cur.execute("SELECT DISTINCT brand FROM cars WHERE seller_id=%s",(uid,)); brands=[r['brand'] for r in cur.fetchall()]
    cur.execute("SELECT DISTINCT model_year FROM cars WHERE seller_id=%s",(uid,)); years=[r['model_year'] for r in cur.fetchall()]
    cur.close(); cnx.close()
    return render_template('seller_dashboard.html', mycars=mycars, orders=orders, brands=brands, years=years)


@app.route('/seller/add', methods=['GET','POST'])
def seller_add():
    if session.get('role')!='seller': return redirect(url_for('login'))
    if request.method=='POST':
        uid=session['user_id']
        data={k:request.form.get(k) for k in ('brand','model','model_year','milage','fuel_type','engine','transmission','ext_col','int_col','accident','clean_title','price')}
        cnx=get_db(); cur=cnx.cursor()
        cur.execute("""INSERT INTO cars (seller_id, brand, model, model_year, milage, fuel_type, engine, transmission, ext_col, int_col, accident, clean_title, price, is_approved)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)""", (uid, data['brand'], data['model'], data['model_year'] or 0, data['milage'], data['fuel_type'], data['engine'], data['transmission'], data['ext_col'], data['int_col'], data['accident'], data['clean_title'], data['price']))
        cnx.commit(); cur.close(); cnx.close()
        flash('Car added for admin approval','success'); return redirect(url_for('seller_dashboard'))
    return render_template('seller_add.html')

# Buyer dashboard - shows approved cars with assigned seller (and includes json-based dataset)
@app.route('/buyer')
def buyer_dashboard():
    if session.get('role')!='buyer': return redirect(url_for('login'))
    brand_filter=request.args.get('brand'); year_filter=request.args.get('year'); search=request.args.get('q','').strip()
    cnx=get_db(); cur=cnx.cursor(dictionary=True)
    sql = """SELECT c.*, u.name as seller_name, u.phone as seller_phone FROM cars c JOIN users u ON c.seller_id=u.id WHERE c.is_approved=1"""
    params = []
    if brand_filter: sql += " AND c.brand=%s"; params.append(brand_filter)
    if year_filter: sql += " AND c.model_year=%s"; params.append(year_filter)
    if search: sql += " AND (c.model LIKE %s OR c.brand LIKE %s)"; params.extend([f"%{search}%", f"%{search}%"])
    cur.execute(sql, tuple(params))
    cars = cur.fetchall()
    try:
        with open(DATA_FILE,'r',encoding='utf-8') as f: j=json.load(f); brands_json=sorted({(c.get('brand') or '').strip() for c in j if c.get('brand')})
    except: brands_json=[]
    cur.execute("SELECT DISTINCT brand FROM cars WHERE brand IS NOT NULL AND brand<>''"); brands_db=[r['brand'] for r in cur.fetchall()]
    brands=sorted(set(brands_db+brands_json))
    cur.execute("SELECT DISTINCT model_year FROM cars WHERE model_year IS NOT NULL AND model_year<>0"); years=[r['model_year'] for r in cur.fetchall()]
    cur.close(); cnx.close()
    return render_template('buyer_dashboard.html', cars=cars, brands=brands, years=years, sel_brand=brand_filter, sel_year=year_filter, q=search)

# Request order route
@app.route('/request_order/<int:car_id>', methods=['GET','POST'])
def request_order(car_id):
    if session.get('role')!='buyer': return redirect(url_for('login'))
    cnx=get_db(); cur=cnx.cursor(dictionary=True)
    cur.execute("SELECT id, brand, model, seller_id FROM cars WHERE id=%s",(car_id,))
    car=cur.fetchone()
    if not car:
        cur.close(); cnx.close(); flash('Car not found','danger'); return redirect(url_for('buyer_dashboard'))
    if not car.get('seller_id'):
        cur.close(); cnx.close(); flash('Seller not available for this car - admin must assign a seller before it can be requested.','warning'); return redirect(url_for('buyer_dashboard'))
    if request.method=='POST':
        buyer_name=request.form.get('buyer_name'); buyer_phone=request.form.get('buyer_phone')
        buyer_address=request.form.get('buyer_address'); delivery_date=request.form.get('delivery_date') or None
        buyer_id=session['user_id']
        cur2=cnx.cursor()
        cur2.execute("INSERT INTO orders (buyer_id, car_id, seller_id, buyer_name, buyer_phone, buyer_address, delivery_date, status) VALUES (%s,%s,%s,%s,%s,%s,%s,'pending')",(buyer_id, car_id, car.get('seller_id'), buyer_name, buyer_phone, buyer_address, delivery_date))
        cnx.commit(); cur2.close(); cur.close(); cnx.close()
        flash('Request submitted to admin for approval','success'); return redirect(url_for('buyer_dashboard'))
    cur.close(); cnx.close()
    return render_template('request_form.html', car=car)

@app.route('/my_requests')
def my_requests():
    if session.get('role')!='buyer': return redirect(url_for('login'))
    uid=session['user_id']; cnx=get_db(); cur=cnx.cursor(dictionary=True)
    cur.execute("SELECT o.*, c.brand, c.model, u.name as seller_name FROM orders o JOIN cars c ON o.car_id=c.id LEFT JOIN users u ON c.seller_id=u.id WHERE o.buyer_id=%s",(uid,))
    orders=cur.fetchall(); cur.close(); cnx.close()
    return render_template('my_requests.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)
