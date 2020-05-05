from hotline.database import models as db


def create_event(create_primary_number=True):
    number = db.Number()
    number.number = "5678"
    number.country = "US"
    number.features = ""
    number.save()

    event = db.Hotline()
    event.name = "Test event"
    event.slug = "test"
    event.owner_user_id = "abc123"

    if create_primary_number:
        event.primary_number = number.number
        event.primary_number_id = number

    event.save()

    return event


# TODO NZ: rename method to member (single)
# TODO NZ: fix verified spelled wrong
def add_unverfied_members(event):
    member = db.HotlineMember()
    member.name = "Unverified Judy"
    member.number = "303"
    member.event = event
    member.verified = False
    member.save()

    return member


def add_members(event):
    members = []

    member = db.HotlineMember()
    member.name = "Bob"
    member.number = "101"
    member.event = event
    member.verified = True
    member.save()
    members.append(member)

    member = db.HotlineMember()
    member.name = "Alice"
    member.number = "202"
    member.event = event
    member.verified = True
    member.save()
    members.append(member)

    return members


def create_block_list(event, number, blocked_by):
    db.BlockList.create(event=event, number=number, blocked_by=blocked_by)
