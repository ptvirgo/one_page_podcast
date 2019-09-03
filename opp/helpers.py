from cleantext import clean
import random
import string
from werkzeug.utils import secure_filename

# Helper functions must:
# - stand alone: do not import other parts of the opp library
# - contain no free variables: all variables are bound in the function head
# - not mutate their inputs


def random_text(n):
    """
    Produce a random string of letters and numbers

    Args:
        n - length of the string

    Return:
        a string of ascii letters and numbers
    """
    return ''.join(random.choice(string.ascii_letters + string.digits)
                   for _ in range(n))


def audio_file_name(published, title, audio_format):
    """
    Produce a standardized file name for audio files
    """
    day = published.strftime("%Y-%m-%d")
    extension = audio_format.value
    name = clean(title, no_punct=True).replace(' ', '_')
    return secure_filename("%s-%s.%s" % (day, name, extension))
