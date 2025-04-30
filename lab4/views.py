from marshmallow import ValidationError

from schemas import BookSchema
from models import db, Book
from flask import request, jsonify, Blueprint

book_schema = BookSchema()
books_schema = BookSchema(many=True)
main = Blueprint("main", __name__)


@main.route("/")
def index():
    return jsonify({"message": "Main paige!"})


@main.route('/books', methods=['POST'])
def create_book():
    data = request.get_json()
    try:
        validated_book_data = book_schema.load(data)
        book = Book(**validated_book_data)
        db.session.add(book)
        db.session.commit()
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 422
    return jsonify(book_schema.dump(book)), 201


@main.route("/books", methods=["GET"])
def get_books():
    limit = request.args.get("limit", default=2, type=int)
    cursor = request.args.get("cursor", default=0, type=int)

    query = Book.query.order_by(Book.id)
    if cursor:
        query = query.filter(Book.id > cursor)

    books = query.limit(limit + 1).all()

    has_more = len(books) > limit
    result_books = books[:limit] if has_more else books
    next_cursor = result_books[-1].id if result_books and has_more else None

    return jsonify({
        "books": books_schema.dump(result_books),
        "next_cursor": next_cursor
    })


@main.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = db.get_or_404(Book, book_id)
    return jsonify(book_schema.dump(book)), 200


@main.route("/books/<book_id>", methods=["DELETE"])
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)
    db.session.delete(book)
    db.session.commit()
    return {}, 204