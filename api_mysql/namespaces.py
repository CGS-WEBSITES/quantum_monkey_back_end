from blueprint_imports import (
    sender,
    user,
    contact,
    assets,
    email_list_ns,
)


def add_namespaces(api):
    api.add_namespace(user, "/users")
    api.add_namespace(contact, "/contacts")
    api.add_namespace(email_list_ns, "/lists")
    api.add_namespace(sender, "/email_sender")
    api.add_namespace(assets, "/assets")
    return api

