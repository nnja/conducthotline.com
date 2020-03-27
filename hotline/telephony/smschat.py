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

"""Implements an SMS-based chatroom.

This uses the database as well as the abstract chatroom to build an SMS-based
chat room. This is further tailored specifically to the conduct hotline by
initiating a *new* chatroom when a reporter messages an event's number.
"""

import logging

import hotline.chatroom
from hotline import audit_log, common_text
from hotline.database import highlevel as db
from hotline.database import models
from hotline.telephony import lowlevel
import nexmo


class SmsChatError(Exception):
    pass


class EventDoesNotExist(SmsChatError):
    pass


class NumberBlocked(SmsChatError):
    pass


class NoOrganizersAvailable(SmsChatError):
    pass


class NoRelaysAvailable(SmsChatError):
    pass


def _send_sms_no_fail(*args, **kwargs):
    """Sends an SMS but does not raise an exception if an error occurs,
    instead, it just logs the exception."""
    try:
        hotline.telephony.lowlevel.send_sms(*args, **kwargs)
    except nexmo.ClientError:
        logging.exception("Failed to send message for SMS relay.")


def handle_sms_chat_error(err: SmsChatError, sender: str, relay: str):
    if isinstance(err, EventDoesNotExist):
        lowlevel.send_sms(sender=relay, to=sender, message=common_text.sms_no_event)
    elif isinstance(err, NumberBlocked):
        pass
    elif isinstance(err, NoOrganizersAvailable):
        lowlevel.send_sms(sender=relay, to=sender, message=common_text.sms_no_members)
    elif isinstance(err, NoRelaysAvailable):
        lowlevel.send_sms(sender=relay, to=sender, message=common_text.sms_no_relays)
