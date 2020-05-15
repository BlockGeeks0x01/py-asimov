from setuptools import (
    setup,
    find_packages,
)

with open("README.md", "r") as f:
    long_description = f.read()


extras_require = {
    'test': [
        "pytest>=5.2.2,<6",
        "pytest-cov>=2.8.1,<3",
        "tox>=3.15.0,<4",
    ],
    'lint': [
        "pylint>=2.5.2,<3",
    ],
    'doc': [
        "Sphinx>=1.8.5,<2",
        "sphinx-rtd-theme>=0.4.3,<1",
    ],
    'dev': [
        "pytest-watch>=4.2.0,<5",
        "ipython",
        "wheel",
        "twine",
        "bump2version>=1.0.0,<2",
    ]
}

extras_require['dev'] = (
    extras_require['dev'] +
    extras_require['test'] +
    extras_require['doc']
)

setup(
    name="py-asimov",
    version='0.3.0',
    keywords="asimov",
    description="""sdk for asimov chain""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT License",
    author="The Asimov Foundation",
    author_email="ericsgy@163.com",
    include_package_data=True,
    url="https://github.com/AsimovNetwork/asimovpy-lib",
    install_requires=[
        "fastecdsa>=1.7.4,<2",
        "web3>=4.9.0,<5",
        "python-bitcointx>=1.0.1,<2",
        "requests>=2.22.0,<3",
        "py-solc>=3.2.0,<4",
    ],
    python_requires=">=3.6, <4",
    extras_require=extras_require,
    zip_safe=False,
    py_modules=['asimov'],
    packages=find_packages(exclude=["test", "test.*"]),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.6',
    ],
)
