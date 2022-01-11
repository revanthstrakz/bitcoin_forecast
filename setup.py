from setuptools import find_namespace_packages, setup

setup(
    name="bitcoin_forecast",
    version="1.0",
    description="A bitcoin forecast package",
    author="Man Foo",
    author_email="foomail@foo.com",
    package_dir={"": "src"},
    packages=find_namespace_packages("src", exclude=["notebooks*", "local*", "dist*", "build*"]),  # same as name
    # install_requires=["wheel", "bar", "greek"],  # external packages as dependencies
)
