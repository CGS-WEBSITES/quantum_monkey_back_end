# Imports de blueprints
from blueprint_imports import *


def add_namespaces(api):
    # End-points
    api.add_namespace(user, "/users")
    api.add_namespace(role, "/roles")
    api.add_namespace(party_role, "/party_roles")
    api.add_namespace(country, "/countries")
    api.add_namespace(sku, "/skus")
    api.add_namespace(campaign, "/campaigns")
    api.add_namespace(store, "/stores")
    api.add_namespace(event, "/events")
    api.add_namespace(libraries, "/libraries")
    api.add_namespace(friends, "/friends")
    api.add_namespace(event_status, "/event_status")
    api.add_namespace(season, "/seasons")
    api.add_namespace(scenery, "/sceneries")
    api.add_namespace(images, "/images")
    api.add_namespace(reward, "/rewards")
    api.add_namespace(relationship, "/rl_campaigns_users")
    api.add_namespace(rl_events_users, "/rl_events_users")
    api.add_namespace(rl_events_rewards, "/rl_events_rewards")
    api.add_namespace(rl_users_rewards, "/rl_users_rewards")

    return api
