"""Install Scoreboard web app."""

from setuptools import setup, find_packages

setup(
    name="Chainball WebBoard",
    version="1.0",
    packages=find_packages(),
    install_requires=["Quart"],
    package_data={"web_board": ["static/dist/*", "templates/*.html"]},
    author="Bruno Morais",
    author_email="brunosmmm@gmail.com",
    description="WebBoard for The Chainball Scoreboard",
)
