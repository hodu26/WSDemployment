from flask import jsonify, request
from . import api_blueprint
from ..models.model import User, db
from ..schemas.schema import UserSchema

user_schema = UserSchema()
users_schema = UserSchema(many=True)

@api_blueprint.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify(users_schema.dump(users))

@api_blueprint.route('/users', methods=['POST'])
def add_user():
    data = request.get_json()
    errors = user_schema.validate(data)

    if errors:
        return jsonify(errors), 400

    new_user = User(
        username=data['username'],
        email=data['email'],
        age=data.get('age')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(user_schema.dump(new_user)), 201
