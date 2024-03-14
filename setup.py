from setuptools import find_packages, setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()
setup(
    name='llm-banya',
    packages=find_packages(),
    version='0.0.1',
    description='',
    author='',
    author_email='',
    url='',
    download_url='z',
    keywords=[],
    install_requires=requirements,
    classifiers=[],
)
