"""Utilities."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
from urllib.parse import urlparse, urljoin
from quart import request, url_for


class LoginForm(FlaskForm):
    """Simple login form."""

    user_name = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])


def is_safe_url(target):
    """Check if url is safe."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (
        test_url.scheme in ("http", "https")
        and ref_url.netloc == test_url.netloc
    )
