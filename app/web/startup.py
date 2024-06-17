from flask import Flask
from app.web.home.home_page import home_page
from app.web.detail.detail_page import detail_page
from rich.logging import RichHandler
import rich
import logging

rich.get_console().set_alt_screen(False)
rich.get_console().clear()
logging.basicConfig(
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(message)s",
    handlers=[
        RichHandler(
            tracebacks_show_locals=True,
            rich_tracebacks=True,
            tracebacks_word_wrap=True,
            tracebacks_suppress=["logging"],
        )
    ],
)


def create_app():
    app = Flask(__name__)

    app.register_blueprint(home_page)
    app.register_blueprint(detail_page, url_prefix="/detail")

    return app
