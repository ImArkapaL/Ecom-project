import psycopg2
from psycopg2 import sql

def create_tables():
    # Connect to your PostgreSQL database
    conn = psycopg2.connect("dbname=your_database_name user=your_username password=your_password")
    cursor = conn.cursor()

    # SQL commands to create tables
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        address VARCHAR(255),
        phone_number VARCHAR(15),
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_user_details_table = """
    CREATE TABLE IF NOT EXISTS user_details (
        user_id INT PRIMARY KEY,
        email VARCHAR(100) UNIQUE NOT NULL,
        date_of_birth DATE,
        phone_number VARCHAR(15),
        address VARCHAR(255),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """

    create_products_table = """
    CREATE TABLE IF NOT EXISTS products (
        product_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        stock INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

    create_cart_table = """
    CREATE TABLE IF NOT EXISTS cart (
        cart_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
        UNIQUE (user_id, product_id)  -- Ensure a user can only have one entry per product
    );
    """

    create_orders_table = """
    CREATE TABLE IF NOT EXISTS orders (
        order_id SERIAL PRIMARY KEY,
        user_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL,
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(50) DEFAULT 'Pending',
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    );
    """

    # Execute the SQL commands
    cursor.execute(create_users_table)
    cursor.execute(create_user_details_table)
    cursor.execute(create_products_table)
    cursor.execute(create_cart_table)
    cursor.execute(create_orders_table)

    # Commit the changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()