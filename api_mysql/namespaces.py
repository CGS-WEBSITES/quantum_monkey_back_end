from blueprint_imports import (
    sender,
    user,
    contact,
    assets,
    login,
)


def add_namespaces(api):
    api.add_namespace(user, "/users")
    api.add_namespace(contact, "/contacts")
    api.add_namespace(sender, "/email_sender")
    api.add_namespace(assets, "/assets")
    api.add_namespace(login, "/login")
    return api
