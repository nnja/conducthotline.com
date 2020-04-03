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

import logging

import flask
import hotline.database.ext
from hotline import csrf, injector
from hotline.telephony import lowlevel, verification, voice

blueprint = flask.Blueprint("telephony", __name__)
hotline.database.ext.init_app(blueprint)


HOLD_MUSIC = "https://assets.ctfassets.net/j7pfe8y48ry3/530pLnJVZmiUu8mkEgIMm2/dd33d28ab6af9a2d32681ae80004886e/oaklawn-dreams.mp3"


@csrf.exempt
@blueprint.route("/telephony/inbound-call", methods=["POST"])
@injector.needs("nexmo.client")
def inbound_call(client):
    call = flask.request.get_json()
    event_number = lowlevel.normalize_e164_number(call["to"])
    reporter_number = lowlevel.normalize_e164_number(call["from"])
    conversation_uuid = call["conversation_uuid"]
    call_uuid = call["uuid"]

    ncco = voice.handle_inbound_call(
        reporter_number=reporter_number,
        event_number=event_number,
        conversation_uuid=conversation_uuid,
        call_uuid=call_uuid,
        host=flask.request.host,
    )

    return flask.jsonify(ncco)


@csrf.exempt
@blueprint.route(
    "/telephony/connect-to-conference/<origin_conversation_uuid>/<origin_call_uuid>",
    methods=["POST"],
)
@injector.needs("nexmo.client")
def connect_to_conference(origin_conversation_uuid, origin_call_uuid, client):
    call = flask.request.get_json()
    member_number = lowlevel.normalize_e164_number(call["to"])
    event_number = lowlevel.normalize_e164_number(call["from"])

    ncco = voice.handle_member_answer(
        event_number=event_number,
        member_number=member_number,
        origin_conversation_uuid=origin_conversation_uuid,
        origin_call_uuid=origin_call_uuid,
    )

    return flask.jsonify(ncco)


@csrf.exempt
@blueprint.route("/telephony/event", methods=["POST"])
def event():
    # For now, we do nothing with these events, but this is required by
    # nexmo.
    return "", 204
