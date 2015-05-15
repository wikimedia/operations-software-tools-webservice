from setuptools import setup, find_packages

setup(
    name='tools-webservice',
    version='0.1',
    author='Yuvi Panda',
    author_email='yuvipanda@gmail.com',
    packages=find_packages(),
    scripts=[
        'scripts/webservice-runner',
        'scripts/webservice-new',
    ],
    description='Infrastructure for running webservices on tools.wmflabs.org',
    install_requires=[
        'PyYAML'
    ]
)
