import string
import random

def generate_short_code(length=6):
    """
    Generates a random alphanumeric string of a given length.
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
