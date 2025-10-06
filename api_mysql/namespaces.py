from blueprint_imports import (
    sender,
    user,
    contact,
)


def add_namespaces(api):
    api.add_namespace(user, "/users")
    api.add_namespace(contact, "/contacts")
    api.add_namespace(sender, "/email_sender")
    return api
