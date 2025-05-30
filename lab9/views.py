from marshmallow import ValidationError

from schemas import BookSchema
from models import db, Book
from flask import request, jsonify, Blueprint, url_for

book_schema = BookSchema()
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
    limit = request.args.get('limit', default=3, type=int)
    offset = request.args.get('offset', default=0, type=int)

    total_books = Book.query.count()

    books_stmt = db.select(Book).order_by(Book.title.desc()).limit(limit).offset(offset)
    books = db.session.scalars(books_stmt).all()

    next_url = (
        url_for("main.get_books", limit=limit, offset=offset + limit)
        if offset + limit < total_books else None
    )

    previous_url = (
        url_for("main.get_books", offset=max(offset - limit, 0), limit=limit)
        if offset > 0 else None
    )

    return jsonify({
        "next_url": next_url,
        "previous_url": previous_url,
        "total_books": total_books,
        "books": BookSchema(many=True).dump(books)
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
