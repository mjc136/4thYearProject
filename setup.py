from setuptools import setup, find_packages

setup(
    name="bot",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "setuptools",
        "wheel",
        "aiohttp",
        "botbuilder-core",
        "azure-appconfiguration",
        "python-dotenv"
    ]
)

