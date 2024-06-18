from flask import Blueprint, render_template, request, redirect, url_for
from app.domains.publications import (
    search,
    ConditionsSearch,
    SearchOrderBy,
    DateTimeSearch,
    save as publication_save,
)
import base64
from datetime import datetime
from ast import literal_eval

home_page = Blueprint("home", __name__, template_folder="templates")


@home_page.route("/")
async def index():
    filter = request.args

    conditions = ConditionsSearch()

    conditions.hidden = bool(int(filter.get("hidden", 0)))
    conditions.deleted = bool(int(filter.get("deleted", 0)))
    if filter.get("favorited") is not None:
        conditions.favorited = bool(int(filter.get("favorited")))

    if filter.get("created_at"):
        created_at = datetime.strptime(filter.get("created_at"), "%Y-%m-%d")
        conditions.created_at = DateTimeSearch(
            back=datetime.now() - created_at
        )
    if filter.get("updated_at"):
        updated_at = datetime.strptime(filter.get("updated_at"), "%Y-%m-%d")
        conditions.updated_at = DateTimeSearch(
            back=datetime.now() - updated_at
        )
    if filter.get("publication_created_at"):
        publication_created_at = datetime.strptime(
            filter.get("publication_created_at"), "%Y-%m-%d"
        )
        conditions.publication_created_at = DateTimeSearch(
            back=datetime.now() - publication_created_at
        )
    if filter.get("publication_updated_at"):
        publication_updated_at = datetime.strptime(
            filter.get("publication_updated_at"), "%Y-%m-%d"
        )
        conditions.publication_updated_at = DateTimeSearch(
            back=datetime.now() - publication_updated_at
        )

    ordering_list = []
    if filter.get("order_by"):
        ordering_list.append(
            SearchOrderBy(
                field=filter.get("order_by"),
                direction=filter.get("direction", "DESC"),
            )
        )

    count, publications = search(
        like=filter.get("like"),
        conditions=conditions,
        ordering=ordering_list,
    )

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
        filter=filter,
    )


@home_page.route("/favorited")
async def favorited():
    publication_save(
        {
            "url": request.args.get("url"),
            "favorited": bool(int(request.args.get("favorited", 0))),
        }
    )
    return redirect(
        url_for("home.index", **literal_eval(request.args.get("filter", "{}")))
    )


@home_page.route("/hidden")
async def hidden():
    publication_save(
        {
            "url": request.args.get("url"),
            "hidden": bool(int(request.args.get("hidden", 0))),
        }
    )
    return redirect(
        url_for("home.index", **literal_eval(request.args.get("filter", "{}")))
    )
