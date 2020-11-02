import setuptools

with open("./README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ccdl", 
    version="0.1.4",
    author="vircoys",
    author_email="vircoys@gmail.com",
    description="Online comic downloader",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vircoys/ccdl",
    license="unlicense",
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    classifiers=[
        "Topic :: Multimedia :: Graphics",
        "Programming Language :: Python :: 3",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)