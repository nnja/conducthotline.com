from hotline.database import models as db


def create_event(create_primary_number=True):
    number = db.Number()
    number.number = "+5678"
    number.country = "US"
    number.features = ""
    number.save()

    event = db.Event()
    event.name = "Test event"
    event.slug = "test"
    event.owner_user_id = "abc123"

    if create_primary_number:
        event.primary_number = number.number
        event.primary_number_id = number

    event.save()

    return event


def add_member(event, name, number, verified=True):

    member = db.EventMember()
    member.name = name
    member.number = number
    member.event = event
    member.verified = verified
    member.save()
    return member


# TODO NZ: rename method to member (single)
# TODO NZ: fix verified spelled wrong
def add_unverfied_members(event):
    member = add_member(
        event=event, name="Unverified Judy", number="303", verified=False,
    )
    return member


def add_members(event):
    members = []

    member = add_member(event=event, name="Bob", number="101",)
    members.append(member)

    member = add_member(event=event, name="Alice", number="202",)

    members.append(member)

    return members


def create_block_list(event, number, blocked_by):
    db.BlockList.create(event=event, number=number, blocked_by=blocked_by)
