#!/usr/bin/env python

import setuptools

requirements = ["apache-airflow", "requests"]

setuptools.setup(
    name="airflow_movielens",
    version="0.1.0",
    description="Hooks, sensors and operators for the Movielens API.",
    author="Anonymous",
    author_email="anonymous@example.com",
    install_requires=requirements,
    packages=setuptools.find_packages("src"),
    package_dir={"": "src"},
    url="https://github.com/mrn-aglic/airflow_book_example_package_repo",
    license="MIT license",
)
