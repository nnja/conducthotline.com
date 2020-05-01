# Copyright 2019 Alethea Katherine Flowers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import flask
import hotline.database.ext
import hotline.telephony.lowlevel
import peewee
from hotline.auth import super_admin_required
from hotline.database import highlevel as db
from hotline.database import models

blueprint = flask.Blueprint("numberadmin", __name__, template_folder="templates")
hotline.database.ext.init_app(blueprint)


@blueprint.route("/admin/numbers")
@super_admin_required
def list():
    numbers = models.Number.select(
        models.Number.number,
        models.Number.country,
        models.Number.features,
        models.Event.name,
        models.Event.slug,
    ).join(
        models.Event,
        peewee.JOIN.LEFT_OUTER,
        on=(models.Event.primary_number_id == models.Number.id),
    )

    return flask.render_template(
        "numberadmin/list.html", numbers=numbers
    )


@blueprint.route("/admin/numbers/<number>/details")
@super_admin_required
def details(number):
    number_entry = models.Number.select().where(models.Number.number == number).get()

    try:
        event = (
            models.Event.select()
            .where(models.Event.primary_number_id == number_entry)
            .get()
        )
    except peewee.DoesNotExist:
        event = None

    info = hotline.telephony.lowlevel.get_number_info(number)

    return flask.render_template(
        "numberadmin/details.html",
        number=number_entry,
        event=event,
        info=info,
    )


@blueprint.route("/admin/numbers/rent", methods=["POST"])
@super_admin_required
def rent():
    country = flask.request.values["country"]

    if not country:
        return flask.abort(400, "Missing country.")

    number = hotline.telephony.lowlevel.rent_number(
        country_code=country,
        sms_callback_url=flask.url_for("telephony.inbound_sms", _external=True),
    )
    number_record = models.Number()
    number_record.number = number["msisdn"]
    number_record.country = number["country"]
    number_record.features = ",".join(number.get("features", []))
    number_record.save()

    return flask.redirect(flask.url_for(".list"))
