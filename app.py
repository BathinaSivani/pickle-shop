from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
from werkzeug.security import generate_password_hash, check_password_hash
import json
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# In-memory storage (replace with database in production)
users = {}
orders = []

# Sample product data
products_data = {
    1: {
        'name': 'Mango Pickle',
        'price': 150,
        'image': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&h=200&fit=crop',
        'description': 'Traditional spicy mango pickle made with fresh ingredients'
    },
    2: {
        'name': 'Lemon Pickle',
        'price': 120,
        'image': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=200&fit=crop',
        'description': 'Tangy lemon pickle with aromatic spices'
    },
    3: {
        'name': 'Mixed Vegetable Pickle',
        'price': 180,
        'image': 'https://images.unsplash.com/photo-1571197110022-14f4e85f4c4c?w=300&h=200&fit=crop',
        'description': 'Assorted vegetables pickled to perfection'
    },
    4: {
        'name': 'Garlic Pickle',
        'price': 140,
        'image': 'https://images.unsplash.com/photo-1599909533607-e1d1e2e2e3f4?w=300&h=200&fit=crop',
        'description': 'Spicy garlic pickle with traditional recipe'
    },
    5: {
        'name': 'Banana Chips',
        'price': 80,
        'image': 'https://images.unsplash.com/photo-1580873435531-d13f5d2e7c5d?w=300&h=200&fit=crop',
        'description': 'Crispy homemade banana chips'
    },
    6: {
        'name': 'Murukku',
        'price': 100,
        'image': 'https://images.unsplash.com/photo-1555681618-85c59b645fdc?w=300&h=200&fit=crop',
        'description': 'Traditional South Indian spiral snack'
    },
    7: {
        'name': 'Tamarind Pickle',
        'price': 160,
        'image': 'https://images.unsplash.com/photo-1584277261846-c6a1672ed2d4?w=300&h=200&fit=crop',
        'description': 'Sweet and tangy tamarind pickle'
    },
    8: {
        'name': 'Coconut Chutney Powder',
        'price': 90,
        'image': 'https://images.unsplash.com/photo-1580635180657-5d6b6d3b0c27?w=300&h=200&fit=crop',
        'description': 'Homemade coconut chutney powder'
    }
}

def generate_order_number():
    """Generate a random order number"""
    return f"ORD-{random.randint(10000, 99999)}"

def generate_tracking_number():
    """Generate a random tracking number"""
    return f"TRK{random.randint(100000, 999999)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    
    if username in users:
        flash('Username already exists!')
        return redirect(url_for('auth'))
    
    users[username] = {
        'email': email,
        'password': generate_password_hash(password),
        'orders': []
    }
    
    session['username'] = username
    flash('Registration successful!')
    return redirect(url_for('products'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    if username in users and check_password_hash(users[username]['password'], password):
        session['username'] = username
        return redirect(url_for('products'))
    
    flash('Invalid username or password!')
    return redirect(url_for('auth'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('cart', None)
    return redirect(url_for('home'))

@app.route('/products')
def products():
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    return render_template('products.html', products=products_data)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    
    session['cart'] = cart
    flash(f'{products_data[product_id]["name"]} added to cart!')
    return redirect(url_for('products'))

@app.route('/cart')
def cart():
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        product = products_data[int(product_id)]
        subtotal = product['price'] * quantity
        total += subtotal
        cart_items.append({
            'id': product_id,
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity,
            'subtotal': subtotal
        })
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session:
        cart = session['cart']
        if str(product_id) in cart:
            del cart[str(product_id)]
            session['cart'] = cart
            flash('Item removed from cart!')
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty!')
        return redirect(url_for('products'))
    
    total = sum(products_data[int(pid)]['price'] * qty for pid, qty in cart.items())
    return render_template('checkout.html', total=total)

@app.route('/process_checkout', methods=['POST'])
def process_checkout():
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty!')
        return redirect(url_for('products'))
    
    # Get customer details
    customer_details = {
        'name': request.form['name'],
        'email': request.form['email'],
        'address': request.form['address'],
        'mobile': request.form['mobile'],
        'payment_method': request.form['payment_method']
    }
    
    # Create cart items for the order
    cart_items = []
    total = 0
    for product_id, quantity in cart.items():
        product = products_data[int(product_id)]
        subtotal = product['price'] * quantity
        total += subtotal
        cart_items.append({
            'id': product_id,
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity,
            'subtotal': subtotal
        })
    
    # Create order
    order_number = generate_order_number()
    tracking_number = generate_tracking_number()
    
    order = {
        'id': len(orders) + 1,
        'order_number': order_number,
        'username': session['username'],
        'items': cart.copy(),
        'cart_items': cart_items,
        'customer_details': customer_details,
        'total': total,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'order_date': datetime.now().strftime('%B %d, %Y'),
        'status': 'confirmed',
        'tracking_number': tracking_number
    }
    
    orders.append(order)
    users[session['username']]['orders'].append(order['id'])
    
    # Store order ID in session for confirmation page
    session['last_order_id'] = order['id']
    
    # Clear cart
    session['cart'] = {}
    
    # Pass all necessary data to template
    return render_template('order_confirmation.html', 
                         order=order,
                         cart_items=cart_items,
                         products=products_data,
                         order_number=order_number,
                         total=total,
                         customer_email=customer_details['email'],
                         shipping_address=customer_details['address'],
                         payment_method=customer_details['payment_method'],
                         tracking_number=tracking_number,
                         order_date=order['order_date'],
                         delivery_date='5-7 Business Days',
                         carrier='Express Delivery',
                         show_popup=True)

@app.route('/order_confirmation')
@app.route('/order_confirmation')
@app.route('/order_confirmation/<order_number>')
def order_confirmation(order_number=None):
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    # Try to get order from URL parameter first, then session
    if order_number:
        order = None
        for o in orders:
            if o['order_number'] == order_number and o['username'] == session['username']:
                order = o
                break
    else:
        # Get the order ID from session
        order_id = session.get('last_order_id')
        if not order_id:
            # Check if user has any orders at all
            user_orders = [order for order in orders if order['username'] == session['username']]
            if user_orders:
                # Redirect to the most recent order
                latest_order = max(user_orders, key=lambda x: x['id'])
                return redirect(url_for('order_confirmation', order_number=latest_order['order_number']))
            else:
                flash('No orders found!')
                return redirect(url_for('products'))
        
        # Find the order by ID
        order = None
        for o in orders:
            if o['id'] == order_id and o['username'] == session['username']:
                order = o
                break
    
    if not order:
        flash('Order not found!')
        return redirect(url_for('products'))
    
    # Create cart items for display
    cart_items = []
    for product_id, quantity in order['items'].items():
        product = products_data[int(product_id)]
        subtotal = product['price'] * quantity
        cart_items.append({
            'id': product_id,
            'name': product['name'],
            'price': product['price'],
            'quantity': quantity,
            'subtotal': subtotal
        })
    
    return render_template('order_confirmation.html', 
                         order=order,
                         cart_items=cart_items,
                         products=products_data,
                         order_number=order['order_number'],
                         total=order['total'],
                         customer_email=order['customer_details']['email'],
                         shipping_address=order['customer_details']['address'],
                         payment_method=order['customer_details']['payment_method'],
                         tracking_number=order['tracking_number'],
                         order_date=order['order_date'],
                         delivery_date='5-7 Business Days',
                         carrier='Express Delivery')

# Keep the old route for backward compatibility
@app.route('/place_order', methods=['POST'])
def place_order():
    return process_checkout()

# Additional routes that your template might reference
@app.route('/track_order')
def track_order():
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    user_orders = [order for order in orders if order['username'] == session['username']]
    return render_template('track_order.html', orders=user_orders)

@app.route('/order_invoice')
def order_invoice():
    if 'username' not in session:
        return redirect(url_for('auth'))
    
    order_id = session.get('last_order_id')
    if not order_id:
        flash('No recent order found!')
        return redirect(url_for('products'))
    
    # Find the order
    order = None
    for o in orders:
        if o['id'] == order_id and o['username'] == session['username']:
            order = o
            break
    
    if not order:
        flash('Order not found!')
        return redirect(url_for('products'))
    
    return render_template('invoice.html', order=order)

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    app.run(debug=True)