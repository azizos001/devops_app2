from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson import ObjectId
import os

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/ecommerce')
mongo = PyMongo(app)

@app.route('/stock/<product_id>', methods=['GET'])
def get_stock(product_id):
    stock = mongo.db.stock.find_one({'product_id': product_id})
    if stock:
        stock['_id'] = str(stock['_id'])
        return jsonify(stock)
    return jsonify({'error': 'Stock not found'}), 404

@app.route('/stock/update', methods=['POST'])
def update_stock():
    data = request.json
    product_id = data['product_id']
    quantity_change = data['quantity_change']
    
    stock = mongo.db.stock.find_one({'product_id': product_id})
    if not stock:
        return jsonify({'error': 'Stock not found'}), 404
    
    new_quantity = stock['quantity'] + quantity_change
    if new_quantity < 0:
        return jsonify({'error': 'Insufficient stock'}), 400
    
    result = mongo.db.stock.update_one(
        {'product_id': product_id},
        {'$set': {'quantity': new_quantity}}
    )
    
    if result.modified_count:
        return jsonify({'status': 'success', 'new_quantity': new_quantity})
    return jsonify({'error': 'Update failed'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)