from setuptools import setup, find_packages

setup(
    name='imputime',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'pandas>=1.0',
        'numpy>=1.18',
    ],
    description='A package for time-series data interpolation and extrapolation.',
    author='Erika Gutierrez',
    author_email='metrionllc@gmail.com',
    url='https://github.com/erikaguti/imputime'
)