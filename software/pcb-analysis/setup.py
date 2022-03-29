from pathlib import Path
from setuptools import setup, find_packages

projectDir = Path(__file__).parent

with open(Path(projectDir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pcb-analysis',
    version='1.0.0',
    description='PROBoter - Visual PCB analysis microservice',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Environment :: Console'
    ],
    keywords='PROBoter pentesting embedded automotive',
    url='https://github.com/schutzwerk/PROBoter',
    author='fweber@SCHUTZWERK GmbH',
    author_email='info@schutzwerk.com',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-restx',
        'tensorflow',
        'opencv-python-headless',
        'pytesseract',
        'flask-cors'
    ],
    python_requires='>=3.8'
)
