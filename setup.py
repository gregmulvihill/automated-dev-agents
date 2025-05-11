from setuptools import setup, find_packages

setup(
    name="automated-dev-agents",
    version="0.1.0",
    description="Automated Development System with Configurable Agents",
    author="Greg Mulvihill",
    author_email="info@cogentecho.ai",
    url="https://github.com/gregmulvihill/automated-dev-agents",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "anthropic>=0.6.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.20.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0"
        ]
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11"
    ],
    python_requires=">=3.10",
)