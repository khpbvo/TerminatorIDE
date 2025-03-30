from setuptools import find_packages, setup

setup(
    name="terminatoride",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "-e ." "pre-commit" "textual",
        "openai",
        "openai-agents",
        "pyte",
        "pexpect",
        "gitpython",
        "paramiko",
        "python-dotenv",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "pytest-mock",
            "black",
            "isort",
            "mypy",
        ],
    },
)
