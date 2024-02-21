from flask import Flask, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS
from flask_jwt import JWT, jwt_required
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

from secure import authenticate, identity

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Migrate(app, db)

class Train(db.Model):
    name = db.Column(db.String(50), primary_key=True)

    def __init__(self, name):
        self.name = name

    def json(self):
        return {'name': self.name}

api = Api(app)
jwt = JWT(app, authenticate, identity)
CORS(app)



class TestView(Resource):
    def get(self):
        return jsonify({'message':'hellow world'})

class BookView(Resource):

    def get(self, name):
        train = Train.query.filter_by(name=name).first()
        if train:
            return train.json()
        else:
            return {'name': None}, 404

    def post(self, name):
        new_train = Train(name=name)
        db.session.add(new_train)
        db.session.commit()
        return new_train.json()
    def delete(self, name):
        train = Train.query.filter_by(name=name).first()
        db.session.delete(train)
        db.session.commit()
        return {'message':'delete success'}

class AllNames(Resource):
    # @jwt_required()
    def get(self):
        trains = Train.query.all()
        return [train.json() for train in trains]

api.add_resource(TestView, '/')
api.add_resource(AllNames, '/all-names/')
api.add_resource(BookView, '/trains/<string:name>/')


if __name__ == '__main__':
    app.run(debug=True)