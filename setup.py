from setuptools import find_packages, setup

setup(
    name="toolforge-webservice",
    version="0.1",
    author="Yuvi Panda",
    author_email="yuvipanda@gmail.com",
    license="Apache2",
    packages=find_packages(),
    scripts=[
        "scripts/webservice-runner",
        "scripts/webservice",
        "scripts/deprecated-tomcat-starter",
    ],
    description="Infrastructure for running webservices on Toolforge",
    install_requires=["PyYAML", "pykube", "six"],
)
