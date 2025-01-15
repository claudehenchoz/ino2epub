from setuptools import setup, find_packages

setup(
    name="ino2epub",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "feedparser",
        "trafilatura>=2.0.0",
        "ebooklib",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml_html_clean>=5.3.0",
    ],
    entry_points={
        'console_scripts': [
            'ino2epub=ino2epub.cli:main',
        ],
    },
    author="Claude Henchoz",
    author_email="claude.henchoz@gmail.com",
    description="Convert Inoreader's read later items to EPUB",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/claudehenchoz/ino2epub",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
