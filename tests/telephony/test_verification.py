from unittest import mock

import nexmo
from hotline import injector
from hotline.database import highlevel as db
from hotline.telephony import verification
from tests.telephony import helpers


@mock.patch("time.sleep", autospec=True)
def test_start_member_verification(sleep, database):
    client = mock.create_autospec(nexmo.Client, instance=True)

    client.application_id = "appid"
    client.send_message.return_value = {"messages": [{"error-text": ""}]}

    injector.set("nexmo.client", client)
    injector.set("secrets.virtual_number", "1234567890")

    event = helpers.create_event()
    member = helpers.add_unverfied_members(event)

    verification.start_member_verification(member)

    expected_msg = (
        f"You've been added as a member of the {member.hotline.name} hotline on friendhotline.com."
        " Reply with YES or OK to confirm."
    )

    client.send_message.assert_called_once_with(
        {"from": event.primary_number, "to": member.number, "text": expected_msg}
    )


@mock.patch("time.sleep", autospec=True)
def test_start_member_verification_no_primary_event_number(sleep, database):
    client = mock.create_autospec(nexmo.Client, instance=True)

    client.application_id = "appid"
    client.send_message.return_value = {"messages": [{"error-text": ""}]}

    injector.set("nexmo.client", client)

    hotline_virtual_number = "1234567890"
    injector.set("secrets.virtual_number", hotline_virtual_number)

    event = helpers.create_event(create_primary_number=False)
    member = helpers.add_unverfied_members(event)

    verification.start_member_verification(member)

    expected_msg = (
        f"You've been added as a member of the {member.hotline.name} hotline on friendhotline.com."
        " Reply with YES or OK to confirm."
    )

    client.send_message.assert_called_once_with(
        {"from": hotline_virtual_number, "to": member.number, "text": expected_msg}
    )


@mock.patch("time.sleep", autospec=True)
def test_handle_verification_affirmative_message(sleep, database):
    client = mock.create_autospec(nexmo.Client, instance=True)

    client.application_id = "appid"
    client.send_message.return_value = {"messages": [{"error-text": ""}]}

    injector.set("nexmo.client", client)

    hotline_virtual_number = "1234567890"
    injector.set("secrets.virtual_number", hotline_virtual_number)

    event = helpers.create_event()

    responses = ("ok", "yes", "okay")
    for response in responses:
        member = helpers.add_unverfied_members(event)
        verification.maybe_handle_verification(member.number, response)

        member = db.get_member_by_number(member.number)
        assert member.verified

        expected_msg = "Thank you, your number is confirmed."
        client.send_message.assert_called_with(
            {"from": event.primary_number, "to": member.number, "text": expected_msg}
        )


@mock.patch("time.sleep", autospec=True)
def test_handle_verification_negative_message(sleep, database):
    client = mock.create_autospec(nexmo.Client, instance=True)

    client.application_id = "appid"
    client.send_message.return_value = {"messages": [{"error-text": ""}]}

    injector.set("nexmo.client", client)

    hotline_virtual_number = "1234567890"
    injector.set("secrets.virtual_number", hotline_virtual_number)

    event = helpers.create_event()

    responses = ("nyet", "nay", "no way")
    for response in responses:
        member = helpers.add_unverfied_members(event)
        verification.maybe_handle_verification(member.number, response)

        member = db.get_member_by_number(member.number)
        assert not member.verified

        client.send_message.assert_not_called()
