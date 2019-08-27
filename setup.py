from distutils.core import setup

setup(
    name="one_page_podcast",
    version="0.1.0",
    description="Produce a single-page podcast.",
    author="Pablo Virgo",
    author_email="mailbox@pablovirgo.com",
    url="https://github.com/ptvirgo/one_page_podcast",
    packages=["opp"],
    scripts=["opp_manage.py"]
    )
