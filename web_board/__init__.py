"""Chainball Web Board."""

from quart import Quart


def create_app(test_config=None):
    app = Quart(
        __name__,
        instance_relative_config=True,
        static_folder="static/dist",
        static_url_path="/dist",
    )

    from web_board import referee

    app.register_blueprint(referee.bp)
    app.add_url_rule("/", endpoint="index")
    return app
