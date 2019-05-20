"""Chainball Web Board."""

from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    from web_board import referee

    app.register_blueprint(referee.bp)
    app.add_url_rule("/", endpoint="index")
