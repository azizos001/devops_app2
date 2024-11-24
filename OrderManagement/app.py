from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson import ObjectId
import requests
import os

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/ecommerce')
mongo = PyMongo(app)

STOCK_SERVICE = os.getenv('STOCK_SERVICE_URL', 'http://stock-manager:5002')
PRODUCT_SERVICE = os.getenv('PRODUCT_SERVICE_URL', 'http://product-catalogue:5001')

@app.route('/orders', methods=['POST'])
def create_order():
    order_data = request.json
    
    # Validate stock for all items
    for item in order_data['items']:
        stock_response = requests.get(f"{STOCK_SERVICE}/stock/{item['product_id']}").json()
        if stock_response.get('quantity', 0) < item['quantity']:
            return jsonify({'status': 'error', 'message': 'Insufficient stock'})
    
    # Update stock
    for item in order_data['items']:
        requests.post(f"{STOCK_SERVICE}/stock/update", 
                     json={'product_id': item['product_id'], 
                          'quantity_change': -item['quantity']})
    
    # Create order
    order_data['status'] = 'pending'
    result = mongo.db.orders.insert_one(order_data)
    
    return jsonify({'status': 'success', 'order_id': str(result.inserted_id)})

@app.route('/orders/<user_id>', methods=['GET'])
def get_user_orders(user_id):
    orders = list(mongo.db.orders.find({'user_id': user_id}))
    for order in orders:
        order['_id'] = str(order['_id'])
    return jsonify(orders)

@app.route('/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    status = request.json['status']
    result = mongo.db.orders.update_one(
        {'_id': ObjectId(order_id)},
        {'$set': {'status': status}}
    )
    if result.modified_count:
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Order not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)