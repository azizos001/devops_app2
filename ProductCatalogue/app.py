from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from bson import ObjectId
import os

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/ecommerce')
mongo = PyMongo(app)

@app.route('/products', methods=['GET'])
def get_products():
    products = list(mongo.db.products.find())
    for product in products:
        product['_id'] = str(product['_id'])
    return jsonify(products)

@app.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    if product:
        product['_id'] = str(product['_id'])
        return jsonify(product)
    return jsonify({'error': 'Product not found'}), 404

@app.route('/products', methods=['POST'])
def add_product():
    product = request.json
    result = mongo.db.products.insert_one(product)
    return jsonify({'_id': str(result.inserted_id)}), 201

@app.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    product = request.json
    result = mongo.db.products.update_one(
        {'_id': ObjectId(product_id)},
        {'$set': product}
    )
    if result.modified_count:
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Product not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)