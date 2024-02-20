from flask import Flask, jsonify
from flask.views import MethodView
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Define a class-based view
class TestView(MethodView):
    def get(self):
        for i in range(10):
            print(i)
        return jsonify({'message':'hellow world'})

# Register the BooksAPI class as a view
app.add_url_rule('/', view_func=TestView.as_view('test'))

if __name__ == '__main__':
    app.run(debug=True)