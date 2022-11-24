import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()
INSTALL_REQUIRED = (HERE / "requirements.txt").read_text()
SETUP_REQUIRED = (HERE / "setup_requirements.txt").read_text()
TEST_REQUIRED = (HERE / "test_requirements.txt").read_text()
MQTT_EXTRA_REQUIRED = (HERE / "mqtt_extra_requirements.txt").read_text()

setup(
    name='vwsfriend',
    packages=find_packages(),
    version=open("vwsfriend/__version.py").readlines()[-1].split()[-1].strip("\"'"),
    description='',
    long_description=README,
    long_description_content_type="text/markdown",
    author='Till Steinbach',
    keywords='weconnect, we connect, carnet, car net, volkswagen, vw, telemetry, smarthome',
    url='https://github.com/tillsteinbach/VWsFriend',
    project_urls={
        'Funding': 'https://github.com/sponsors/VWsFriend',
        'Source': 'https://github.com/tillsteinbach/VWsFriend',
        'Bug Tracker': 'https://github.com/tillsteinbach/VWsFriend/issues'
    },
    license='MIT',
    install_requires=INSTALL_REQUIRED,
    extras_require={
        "MQTT": MQTT_EXTRA_REQUIRED,
    },
    entry_points={
        'console_scripts': [
            'vwsfriend = vwsfriend.vwsfriend_base:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Utilities',
        'Topic :: System :: Monitoring',
        'Topic :: Home Automation',
    ],
    python_requires='>=3.8',
    setup_requires=SETUP_REQUIRED,
    tests_require=TEST_REQUIRED,
    include_package_data=True,
    zip_safe=False,
)
