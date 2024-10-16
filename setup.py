from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="omegadl",
    version="0.1",
    description="A Comic Downloader and manager for omegascans.",
    package_dir={"":"app"},
    packages=find_packages(where="app"),
    long_description=long_description, 
    long_description_content_type="text/markdown",
    url="https://github.com/sortedcord/omegadl",
    author="sortedcord",
    author_email="mail@adityagupta.dev",
    classifiers= [
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent"
    ],
    install_requires=[
        "requests>=2.32.3",
        "rich>=13.9.2",
        "click>=8.1.7", 
        "pillow>=10.4.0", 
        "numpy>=2.1.2"
    ],
    entry_points={
        'console_scripts': [
            'omegadl = omegadl.cli:cli',
        ],
    },
    python_required=">=3.10"
)