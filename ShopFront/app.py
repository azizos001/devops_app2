from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)
app.secret_key = 'your-secret-key'  # Change this in production

# Service URLs
PRODUCT_SERVICE = os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:5001')
STOCK_SERVICE = os.getenv('STOCK_SERVICE_URL', 'http://localhost:5002')
ORDER_SERVICE = os.getenv('ORDER_SERVICE_URL', 'http://localhost:5003')
USER_SERVICE = os.getenv('USER_SERVICE_URL', 'http://localhost:5004')

@app.route('/')
def index():
    try:
        products = requests.get(f'{PRODUCT_SERVICE}/products').json()
        return render_template('index.html', products=products)
    except requests.exceptions.RequestException:
        flash('Unable to fetch products', 'error')
        return render_template('index.html', products=[])

@app.route('/product/<product_id>')
def product_detail(product_id):
    try:
        product = requests.get(f'{PRODUCT_SERVICE}/products/{product_id}').json()
        stock = requests.get(f'{STOCK_SERVICE}/stock/{product_id}').json()
        return render_template('product_detail.html', product=product, stock=stock)
    except requests.exceptions.RequestException:
        flash('Product not found', 'error')
        return redirect(url_for('index'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if 'cart' not in session:
        session['cart'] = []
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        
        try:
            stock = requests.get(f'{STOCK_SERVICE}/stock/{product_id}').json()
            if stock['quantity'] >= quantity:
                session['cart'].append({
                    'product_id': product_id,
                    'quantity': quantity
                })
                flash('Product added to cart', 'success')
            else:
                flash('Not enough stock available', 'error')
        except requests.exceptions.RequestException:
            flash('Error adding product to cart', 'error')
        
        return redirect(url_for('cart'))
    
    # Get cart items details
    cart_items = []
    total = 0
    
    for item in session.get('cart', []):
        try:
            product = requests.get(f'{PRODUCT_SERVICE}/products/{item["product_id"]}').json()
            cart_items.append({
                'product': product,
                'quantity': item['quantity']
            })
            total += product['price'] * item['quantity']
        except requests.exceptions.RequestException:
            continue
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/cart/update', methods=['POST'])
def update_cart():
    data = request.json
    product_id = data.get('product_id')
    quantity = int(data.get('quantity'))
    
    if 'cart' in session:
        for item in session['cart']:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                session.modified = True
                break
    
    return jsonify({'status': 'success'})

@app.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    data = request.json
    product_id = data.get('product_id')
    
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] 
                          if item['product_id'] != product_id]
        session.modified = True
    
    return jsonify({'status': 'success'})

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Please login first'})
    
    cart = session.get('cart', [])
    if not cart:
        return jsonify({'status': 'error', 'message': 'Cart is empty'})
    
    try:
        order_data = {
            'user_id': session['user_id'],
            'items': cart
        }
        response = requests.post(f'{ORDER_SERVICE}/orders', json=order_data)
        order_response = response.json()
        
        if order_response['status'] == 'success':
            session['cart'] = []
            return jsonify({
                'status': 'success',
                'order_id': order_response['order_id']
            })
    except requests.exceptions.RequestException:
        pass
    
    return jsonify({'status': 'error', 'message': 'Order creation failed'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)