import setuptools
import os

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
        "Flask==1.1.2",
        "Flask-Migrate==2.3.1",
        "Flask-Script==2.0.6",
        "Flask-SQLAlchemy==2.5.1",
        "Flask-WTF==0.14.3",
        "Flask-User==1.0.2.2",
        "Flask-JWT-Extended==4.1.0",
        "Flask-Caching==1.10.1",
        "Flask-Cors==3.0.7",
        "flask-expects-json==1.5.0",
        "gevent==1.4.0",
        "pymagnitude==0.1.120",
        "pandas>=1.0.0",
        "cwb-ccc==0.9.16"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: Unix",
    ],
    python_requires='==3.8',
)
