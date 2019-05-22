"""Chainball Web Board."""

from typing import Dict, Optional

import quart.flask_patch
from quart import Quart
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

LOGIN_MANAGER = LoginManager()

DEVELOP = True


class User:
    """User."""

    _USERS: Dict = {}
    _logged_in: str = None

    def __init__(
        self, user_name: str, pass_hash: str, anonymous: Optional[bool] = False
    ):
        """Initialize."""
        self._id = user_name
        self._anonymous = anonymous
        self._passhash = pass_hash
        self._active = False
        self._authenticated = False
        if user_name in User._USERS:
            raise ValueError("user already exists")
        User._USERS[user_name] = self

    @property
    def is_authenticated(self) -> bool:
        """Is authenticated or not."""
        return self._authenticated

    @is_authenticated.setter
    def is_authenticated(self, value: bool):
        """Authenticate."""
        if value:
            if User._logged_in is not None:
                raise RuntimeError("user already logged in")
            User._logged_in = self._id
        else:
            User._logged_in = None
        self._authenticated = value

    @property
    def is_active(self) -> bool:
        """Is active or not."""
        return self._active

    @is_active.setter
    def is_active(self, value: bool):
        """Activate."""
        self._active = value

    @property
    def is_anonymous(self) -> bool:
        """Is anonymous."""
        return self._anonymous

    def get_id(self) -> str:
        """Get id."""
        return self._id

    @classmethod
    def get(cls, user_id: str):
        """Get user object."""
        return cls._USERS.get(user_id)

    @classmethod
    def get_currently_authenticated(cls):
        """Get currently authenticated user."""
        return cls._logged_in

    @property
    def password_hash(self) -> str:
        """Get password hash."""
        return self._passhash


@LOGIN_MANAGER.user_loader
def load_user(user_id):
    """Load user object from id."""
    return User.get(user_id)


def create_app(test_config: Optional[str] = None):
    """Create the app."""
    app = Quart(
        __name__,
        instance_relative_config=True,
        static_folder="static/dist",
        static_url_path="/dist",
    )

    from web_board import referee

    app.register_blueprint(referee.bp)
    app.add_url_rule("/", endpoint="index")

    # we only use 1 default user, which is an
    # administrator (referee privileges)
    _referee = User(
        "referee",
        pass_hash="$2b$12$84FyxZdjqY9wGQKH7yI4R.tRLQjLEcn7knwvXMYuw2KznG2r5NOoK",
    )
    _referee.is_active = True
    app.user_class = User

    # password hashing utilities
    app.bcrypt = Bcrypt(app)

    # secret key
    app.secret_key = b"__DEVELOPMENTPLACEHOLDER__"
    LOGIN_MANAGER.login_view = "referee.login"
    if DEVELOP is True:
        app.config["LOGIN_DISABLED"] = True
    LOGIN_MANAGER.init_app(app)

    return app
