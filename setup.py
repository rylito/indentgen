import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="indentgen",
    version="0.0.3",
    author="Ryli Dunlap",
    author_email="ryli@transvec.com",
    description="A static site generator for Dentmark",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.transvec.com/indentgen",
    packages=setuptools.find_packages(),
    scripts = ['bin/indentgen'],
    install_requires=[
        'dentmark',
        'mako',
        'Pillow'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
