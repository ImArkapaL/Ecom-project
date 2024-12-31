import os
from flask import Flask, request, redirect, url_for, render_template, flash, session
import psycopg2
import bcrypt
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Ensure you have a directory to store product images
UPLOAD_FOLDER = 'static/images/products'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database connection function
def get_db_connection():
    return psycopg2.connect("dbname=yourdbname user=youruser password=yourpassword")

# User Registration
@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    password = request.form['password']
    email = request.form['mail']
    phone_number = request.form['ph-no']
    date_of_birth = request.form['dob']
    address = request.form.get('address', '')  # Optional field

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, address, phone_number, password_hash)
            VALUES (%s, %s, %s, %s) RETURNING user_id
        """, (name, address, phone_number, hashed_password))
        user_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        flash('Sign up successful! You can now log in.', 'success')
        return redirect(url_for('login_page'))
    except Exception as e:
        flash('An error occurred during sign up. Please try again.', 'error')
        print(e)
        return redirect(url_for('signup_page'))

# User Login
@app.route('/login', methods=['POST'])
def login():
    name = request.form['name']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, password_hash FROM users WHERE name = %s", (name,))
    user = cursor.fetchone()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        session['user_id'] = user[0]  # Store user ID in session
        flash('Login successful!', 'success')
        return redirect(url_for('home'))  # Redirect to the home page
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('login_page'))

# Cart Management
def add_to_cart(user_id, product_id, quantity):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT quantity FROM cart WHERE user_id = %s AND product_id = %s
    """, (user_id, product_id))
    existing_item = cursor.fetchone()
    
    if existing_item:
        new_quantity = existing_item[0] + quantity
        cursor.execute("""
            UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s
        """, (new_quantity, user_id, product_id))
    else:
        cursor.execute("""
            INSERT INTO cart (user_id, product_id, quantity)
            VALUES (%s, %s, %s)
        """, (user_id, product_id, quantity))
    
    conn.commit()
    cursor.close()
    conn.close()

def get_cart(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.cart_id, p.product_id, p.name, c.quantity, p.price
        FROM cart c
        JOIN products        p ON c.product_id = p.product_id
        WHERE c.user_id = %s
    """, (user_id,))
    cart_items = cursor.fetchall()
    cursor.close()
    conn.close()
    return cart_items

@app.route('/my_cart')
@login_required
def my_cart():
    user_id = session['user_id']
    cart_items = get_cart(user_id)
    return render_template('pages/my-cart.html', cart_items=cart_items)

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart_route():
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    user_id = session['user_id']
    
    add_to_cart(user_id, product_id, quantity)
    flash('Product added to cart!', 'success')
    return redirect(url_for('products'))

@app.route('/checkout')
@login_required
def checkout():
    user_id = session['user_id']
    cart_items = get_cart(user_id)
    
    # Calculate total amount
    total_amount = sum(item[3] * item[4] for item in cart_items)  # quantity * price
    
    return render_template('pages/checkout.html', cart_items=cart_items, total_amount=total_amount)

@app.route('/confirm_order', methods=['POST'])
@login_required
def confirm_order():
    user_id = session['user_id']
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    total_amount = request.form['total_amount']
    
    # Check if the address is already in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM user_details WHERE user_id = %s", (user_id,))
    user_details = cursor.fetchone()
    
    if user_details:
        # Update the address if it exists
        cursor.execute("""
            UPDATE user_details SET email = %s, phone_number = %s, address = %s
            WHERE user_id = %s
        """, (email, phone, address, user_id))
    else:
        # Insert new user details if not present
        cursor.execute("""
            INSERT INTO user_details (user_id, email, phone_number, address)
            VALUES (%s, %s, %s, %s)
        """, (user_id, email, phone, address))
    
    conn.commit()
    
    # Fetch cart items for the order
    cart_items = get_cart(user_id)
    
    # Prepare order data for Excel
    order_data = []
    for item in cart_items:
        order_data.append({
            'Order ID': None,  # You can generate an order ID if needed
            'User  ID': user_id,
            'Product ID': item[1],
            'Product Name': item[2],
            'Quantity': item[3],
            'Price': item[4],
            'Total Amount': item[3] * item[4],
            'Order Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    # Create a DataFrame from the order data
    df = pd.DataFrame(order_data)

    # Define the Excel file path
    excel_file_path = 'orders.xlsx'

    # Check if the file already exists
    try:
        existing_df = pd.read_excel(excel_file_path)
        # Append new data to the existing DataFrame
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        # If the file does not exist, it will create a new one
        pass

    # Save the DataFrame to an Excel file
    df.to_excel(excel_file_path, index=False)

    # Clear the cart after the order is confirmed
    cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
    conn.commit()

    cursor.close()
    conn.close()

    flash('Order confirmed! Thank you for your purchase.', 'success')
    return redirect(url_for('home'))

# Admin Product Management
@app.route('/admin')
def admin_page():
    return render_template('admin.html')  # Render the admin page

@app.route('/add_product', methods=['POST'])
def add_product():
    # Get product details from the form
    name = request.form['name']
    price = request.form['price']
    stock = request.form['stock']
    description = request.form['description']
    
    # Handle image upload
    image = request.files['image']
    image_filename = image.filename
    image_path = os.path.join(UPLOAD_FOLDER, image_filename)
    image.save(image_path)

    # Insert product into the database
        conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, description, price, stock)
        VALUES (%s, %s, %s, %s) RETURNING product_id
    """, (name, description, price, stock))
    
    product_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    # Generate HTML page for the product
    generate_product_page(product_id, name, description, price, image_filename)

    flash('Product added successfully!', 'success')
    return redirect(url_for('admin_page'))  # Redirect back to the admin page

def generate_product_page(product_id, name, description, price, image_filename):
    # Create an HTML file for the product
    product_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{name}</title>
    </head>
    <body>
        <h1>{name}</h1>
        <img src="/{UPLOAD_FOLDER}/{image_filename}" alt="{name}">
        <p>Price: ${price}</p>
        <p>Stock: {stock}</p>
        <p>Description: {description}</p>
    </body>
    </html>
    """

    # Save the HTML file
    product_file_path = f'templates/products/{product_id}.html'
    with open(product_file_path, 'w') as f:
        f.write(product_html)

# User Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user ID from session
    flash('You have been logged out.', 'success')
    return redirect(url_for('login_page'))

# Home Page
@app.route('/home')
def home():
    return render_template('index.html')  # Render the index.html template

# Products Page
@app.route('/products')
def products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    product_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('products.html', products=product_list)

# Run the application
if __name__ == '__main__':
    app.run(debug=True)