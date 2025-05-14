from flask import Flask
from flask_restful import Api
from flasgger import Swagger
import os

from models import db
from views import BookResource, BookListResource


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI",
                                                      "postgresql://postgres:postgres@db/library_db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config['SWAGGER'] = {
        'title': 'Library API',
        'uiversion': 3,
        'specs_route': '/swagger/',
        'version': '1.0.0',
        'description': 'API for book management'
    }

    db.init_app(app)
    api = Api(app)
    swagger = Swagger(app)

    with app.app_context():
        db.create_all()

    api.add_resource(BookListResource, '/v1/api/books')
    api.add_resource(BookResource, '/v1/api/books/<int:book_id>')

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=True)
