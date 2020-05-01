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

"""Handles low-level telephony-related actions, such as renting numbers and
sending messages."""

import logging
import time

import nexmo
import phonenumbers
from google.api_core import retry
from hotline import injector


def normalize_number(value: str, country: str = "US") -> str:
    number = phonenumbers.parse(value, country)
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def normalize_e164_number(value: str) -> str:
    # Nexmo sends numbers back in e164 format but without the leading +, so adding
    # that should make the parser work regardless of the default country code.
    number = phonenumbers.parse("+" + value, "US")
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


def pretty_print_number(number: str, country: str = "US") -> str:
    parsed = phonenumbers.parse(number, "US")
    return phonenumbers.format_number(
        parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
    )


@injector.provides(
    "nexmo.client",
    needs=[
        "secrets.nexmo.api_key",
        "secrets.nexmo.api_secret",
        "secrets.nexmo.private_key_location",
        "secrets.nexmo.application_id",
    ],
)
def _make_client(api_key, api_secret, private_key_location, application_id):
    return nexmo.Client(
        key=api_key,
        secret=api_secret,
        application_id=application_id,
        private_key=private_key_location,
    )


# TODO NZ can sms callback URL be empty?
# or, am I going to need this later for phone number verification?
@injector.needs("nexmo.client")
def setup_number(
    number: str, country: str, sms_callback_url: str, client: nexmo.Client
):
    client.update_number(
        {
            "msisdn": number,
            "country": country,
            # "moHttpUrl": sms_callback_url,
            "voiceCallbackType": "app",
            "voiceCallbackValue": client.application_id,
        }
    )


@injector.needs("nexmo.client")
def rent_number(
    sms_callback_url: str, client: nexmo.Client, country_code: str = "US"
) -> dict:
    """Rents a number for the given country.

    NOTE: This immediately charges us for the number (for at least a month).
    """

    # Try to get SMS and VOICE numbers first.
    numbers = client.get_available_numbers(
        country_code, {"features": "SMS,VOICE", "type": "mobile-lvn"}
    )

    # If that fails, get a VOICE-only number.
    if not numbers.get("numbers", []):
        numbers = client.get_available_numbers(
            country_code, {"features": "VOICE", "type": "mobile-lvn"}
        )

    error = RuntimeError("No numbers available.")

    for number in numbers.get("numbers", []):
        try:
            client.buy_number(
                {"country": number["country"], "msisdn": number["msisdn"]}
            )

            setup_number(
                number=number["msisdn"],
                country=number["country"],
                sms_callback_url=sms_callback_url,
                client=client,
            )

            # normalize the number. Nexmo sends it back in E164 format *without* the leading +
            number["msisdn"] = normalize_e164_number(number["msisdn"])

            return number

        except nexmo.Error as nexmo_error:
            error = nexmo_error
            continue

    raise error


@injector.needs("nexmo.client")
def get_number_info(number: str, client: nexmo.Client) -> dict:
    return client.get_account_numbers(pattern=number)["numbers"][0]


def _send_sms_retry_predicate(error):
    logging.exception("Error during SMS send")
    if isinstance(error, nexmo.ClientError) and "Throughput Rate Exceeded" in str(
        error
    ):
        return True
    return False


@retry.Retry(
    predicate=_send_sms_retry_predicate, initial=1.0, maximum=1.0, deadline=30.0
)
@injector.needs("nexmo.client")
def send_sms(sender: str, to: str, message: str, client: nexmo.Client) -> dict:
    """Sends an SMS.

    ``sender`` and ``to`` must be in proper long form.
    """
    # This has to be removed at some point. Sleep a little to avoid hitting rate limits.
    time.sleep(0.3)

    # Nexmo is apparently picky about + being in the sender.
    sender = sender.strip("+")

    logging.info(f"Sending from {sender} to {to} message length {len(message)}")

    resp = client.send_message({"from": sender, "to": to, "text": message})

    # Nexmo client incorrectly treats failed messages as successful
    error_text = resp["messages"][0].get("error-text")

    if error_text:
        raise nexmo.ClientError(error_text)

    return resp
