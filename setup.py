from setuptools import setup, find_packages

setup(
    name="EA2-BigData-Preprocessing",
    version="1.0.0",
    description="Preprocesamiento y limpieza de datos en Big Data",
    author="Eduard Paez",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.3",
        "numpy>=1.24.3",
        "openpyxl>=3.1.2",
    ],
    python_requires=">=3.8",
)