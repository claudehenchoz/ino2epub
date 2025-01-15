from setuptools import setup, find_packages

setup(
    name="ino2epub",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "feedparser",
        "trafilatura",
        "ebooklib",
        "requests>=2.31.0",
    ],
    entry_points={
        'console_scripts': [
            'ino2epub=ino2epub.cli:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Convert Inoreader's read later items to EPUB",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ino2epub",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
