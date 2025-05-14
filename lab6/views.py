from flask import request, jsonify
from flask_restful import Resource
from marshmallow import ValidationError

from schemas import BookSchema
from models import db, Book

book_schema = BookSchema()
books_schema = BookSchema(many=True)


class BookListResource(Resource):
    def get(self):
        """
     Get list of books with pagination
        ---
        parameters:
          - in: query
            name: limit
            type: integer
            default: 3
          - in: query
            name: offset
            type: integer
            default: 0
        responses:
          200:
            description: List of books
            schema:
              type: object
              properties:
                books:
                  type: array
                  items:
                    $ref: '#/definitions/Book'
        """

        limit = request.args.get('limit', default=3, type=int)
        offset = request.args.get('offset', default=0, type=int)
        books = Book.query.limit(limit).offset(offset).all()
        return {'books': books_schema.dump(books)}

    def post(self):
        """
         Create a new book
             ---
            parameters:
            - in: body
              name: body
              required: true
              schema:
                 $ref: '#/definitions/Book'
            responses:
              201:
                description: Book created
                  schema:
                      $ref: '#/definitions/Book'
                  400:
                    description: Validation error
                """
        json_data = request.get_json()
        if not json_data:
            return {'message': 'No input data provided'}, 400

        try:
            book_data = book_schema.load(json_data)

            new_book = Book(
                title=book_data['title'],
                author=book_data['author'],
                year=book_data['year']
            )

            db.session.add(new_book)
            db.session.commit()

            return book_schema.dump(new_book), 201

        except ValidationError as err:
            return {'message': 'Validation error', 'errors': err.messages}, 400


class BookResource(Resource):
    def get(self, book_id):
        """
        Get a specific book by ID
        ---
        parameters:
          - in: path
            name: book_id
            type: integer
            required: true
            description: ID of the book to retrieve
        responses:
          200:
            description: The requested book
            schema:
              $ref: '#/definitions/Book'
          404:
            description: Book not found
        """
        book = db.get_or_404(Book, book_id)
        return book_schema.dump(book)

    def delete(self, book_id):
        """
        Delete a specific book by ID
        ---
        parameters:
          - in: path
            name: book_id
            type: integer
            required: true
            description: ID of the book to delete
        responses:
          204:
            description: Book deleted successfully
          404:
            description: Book not found
        """
        book = db.get_or_404(Book, book_id)
        db.session.delete(book)
        db.session.commit()
        return '', 204
