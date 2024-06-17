from flask import Blueprint, render_template, request
from app.domains.publications import py_url
import base64

detail_page = Blueprint("detail", __name__, template_folder="templates")


@detail_page.route("/")
async def index():
    publication = py_url(request.args["url"])
    publication_picture_encoded = base64.b64encode(publication.picture).decode(
        "utf-8"
    )
    picture = "data:image/jpeg;base64," + publication_picture_encoded

    return render_template(
        "details/index.html", publication=publication, picture=picture
    )
