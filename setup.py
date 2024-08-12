from setuptools import setup, find_packages
import opp

setup(
    name="one_page_podcast",
    version=opp.__version__,
    description="Produce a single-page podcast.",
    author="Pablo Virgo",
    author_email="mailbox@pablovirgo.com",
    url="https://github.com/ptvirgo/one_page_podcast",
    packages=find_packages(),
    include_package_data=True,
    package_data={"opp": ["web/templates/*"]},
    entry_points={"console_scripts": ["opp=opp.cli:main"]}
)
