import random
import string

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
