from setuptools import setup, find_packages

setup(
    name="social-content-archiver",
    version="0.1.0",
    description="Archive, analyze and synthesize saved social media content into a structured knowledge base",
    author="Your Name",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    entry_points={
        "console_scripts": [
            "social-archiver=main:cli",
        ],
    },
)
