from setuptools import setup, find_packages

setup(
    name="one_page_podcast",
    version="0.2.1",
    description="Produce a single-page podcast.",
    author="Pablo Virgo",
    author_email="mailbox@pablovirgo.com",
    url="https://github.com/ptvirgo/one_page_podcast",
    packages=find_packages(),
    scripts=["opp_manage.py"],
    include_package_data=True,
    package_data={"opp": [
        "*.yml",
        "templates/*", "templates/admin/*", "templates/default/*",
        "static/*", "static/admin/*", "static/default/*"
        ]}
    )
