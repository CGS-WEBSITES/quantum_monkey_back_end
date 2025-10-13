from resources.users import user
from resources.send_email import sender
from resources.contacts import contact
from resources.s3_images import assets

blueprint_imports = [user, sender, contact, assets ]
