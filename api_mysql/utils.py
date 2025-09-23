from datetime import date, datetime
import string
import random

dateStr = "%Y-%m-%d"
dateType = lambda x: datetime.strptime(x, dateStr).date()

dateTimeStr = "%Y-%m-%d; %I:%M %p"
dateTimeType = lambda x: datetime.strptime(x, dateTimeStr)


def boolean_string(s):
    if s not in {"false", "true"}:
        raise ValueError("Not a valid boolean string")
    return s == "true"


def random_password():

    characterList = ""

    # Adding letters to possible characters
    characterList += string.ascii_letters
    # Adding digits to possible characters
    characterList += string.digits
    # Adding special characters to possible
    # characters
    characterList += string.punctuation

    password = []

    for i in range(8):

        # Picking a random character from our
        # character list
        randomchar = random.choice(characterList)

        # appending a random character to password
        password.append(randomchar)

    random_password = "".join(password)

    return random_password
