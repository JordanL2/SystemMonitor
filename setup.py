import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="systemmonitor",
    version="1.1.0",
    author="Jordan Leppert",
    author_email="jordanleppert@gmail.com",
    description="A tool to log system data to a database, and an API to read it",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JordanL2/SystemMonitor",
    packages=setuptools.find_packages() + setuptools.find_namespace_packages(include=['systemmonitor.*']),
    install_requires=[
        'mariadb',
        'pyyaml',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: LGPL-2.1 License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    entry_points = {'console_scripts': [
        'systemmonitor-push=systemmonitor.monitor:main',
        'systemmonitor-read=systemmonitor.monitorapi:main',
        ], },
)
