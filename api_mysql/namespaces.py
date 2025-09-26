from blueprint_imports import (
    sender, user,
)


def add_namespaces(api):
    api.add_namespace(user, "/users")
    api.add_namespace(sender, "/email_sender")

    return api
