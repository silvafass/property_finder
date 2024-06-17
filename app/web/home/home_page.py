from flask import Blueprint, render_template
from app.domains.publications import search
import base64

home_page = Blueprint("home", __name__, template_folder="templates")


@home_page.route("/")
async def index():
    count, publications = search()

    printscreen_map = {}
    for publication in publications:
        publication_printscreen_encoded = base64.b64encode(
            publication.printscreen
        ).decode("utf-8")
        printscreen_map[publication.url] = (
            "data:image/jpeg;base64," + publication_printscreen_encoded
        )

    return render_template(
        "index.html",
        count=count,
        publications=publications,
        printscreen_map=printscreen_map,
    )
