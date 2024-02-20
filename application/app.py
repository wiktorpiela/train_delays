from flask import Flask, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS

app = Flask(__name__)
api = Api(app)
CORS(app)

books = []

class TestView(Resource):
    def get(self):
        return jsonify({'message':'hellow world'})

class BookView(Resource):

    def get(self, title):
        for book in books:
            if book['title'] == title:
                return book
        return {'title': None}
    def post(self, title):
        book = {'name': title}
        books.append(book)
        return book
    def delete(self, title):
        for index, book, in enumerate(books):
            if book['title'] == title:
                deleted_book = books.pop(index)
                return {'note': 'delete success'}
        return {'note': 'delete unsuccessful'}

class AllNames(Resource):
    def get(self):
        return {'books': books}

api.add_resource(TestView, '/')
api.add_resource(AllNames, '/all-names/')
api.add_resource(BookView, '/books/')


if __name__ == '__main__':
    app.run(debug=True)