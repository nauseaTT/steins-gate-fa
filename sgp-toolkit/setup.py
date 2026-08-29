from setuptools import setup, find_packages

setup(
    name="sgp-toolkit",
    version="0.1.0",
    description="Steins;Gate Persian Localization Toolkit",
    author="Steins;Gate FA Project Team",
    python_requires=">=3.11",
    packages=find_packages(),
    install_requires=[
        "arabic-reshaper>=3.0.0",
        "python-bidi>=0.4.2",
        "charset-normalizer>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "sgp=sgp.cli:main",
        ],
    },
)
