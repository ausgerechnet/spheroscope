import os

import setuptools

here = os.path.abspath(os.path.dirname(__file__))

# description
with open(os.path.join(here, 'README.md')) as f:
    long_description = f.read()

# version
version = {}
with open(os.path.join(here, 'spheroscope', 'version.py')) as f:
    exec(f.read(), version)


setuptools.setup(
    name='spheroscope',
    version=version['__version__'],
    description="a web app for argumentation mining",
    packages=setuptools.find_packages(),
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ausgerechnet/spheroscope",
    install_requires=[
        "Flask>=2.2,<2.3",
        "Flask-SQLAlchemy>=3.0,<3.1",
        "pymagnitude>=0.1.140,<0.2",
        "cwb-ccc>=0.11.7,<0.12",
        "psycopg2-binary>=2.9.5,<3.0"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: Unix",
    ],
    python_requires='>=3.7,<4',
)
