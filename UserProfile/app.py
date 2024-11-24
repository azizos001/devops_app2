from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/ecommerce')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')  # Change in production
mongo = PyMongo(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    
    if mongo.db.users.find_one({'email': data['email']}):
        return jsonify({'error': 'Email already registered'}), 400
    
    user = {
        'email': data['email'],
        'password': generate_password_hash(data['password']),
        'name': data['name'],
        'created_at': datetime.datetime.utcnow()
    }
    
    result = mongo.db.users.insert_one(user)
    
    return jsonify({
        'status': 'success',
        'user_id': str(result.inserted_id)
    }), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = mongo.db.users.find_one({'email': data['email']})
    
    if user and check_password_hash(user['password'], data['password']):
        token = jwt.encode({
            'user_id': str(user['_id']),
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'token': token,
            'user_id': str(user['_id'])
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user:
        user['_id'] = str(user['_id'])
        user.pop('password', None)
        return jsonify(user)
    return jsonify({'error': 'User not found'}), 404

@app.route('/profile/<user_id>', methods=['PUT'])
def update_profile(user_id):
    data = request.json
    if 'password' in data:
        data['password'] = generate_password_hash(data['password'])
    
    result = mongo.db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': data}
    )
    
    if result.modified_count:
        return jsonify({'status': 'success'})
    return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)