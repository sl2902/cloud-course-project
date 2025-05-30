# coding: utf-8

"""
    Files API

    ![Maintained by](https://img.shields.io/badge/Maintained%20by-MLOps%20Club-05998B?style=for-the-badge)  | Helpful Links | Notes | | --- | --- | | [Course Homepage](https://mlops-club.org) | | | [Course Student Portal](https://courses.mlops-club.org) | | | [Course Materials Repo](https://github.com/mlops-club/python-on-aws-course.git) | `mlops-club/python-on-aws-course` | | [Course Reference Project Repo](https://github.com/mlops-club/cloud-course-project.git) | `mlops-club/cloud-course-project` | | [FastAPI Documentation](https://fastapi.tiangolo.com/) | | | [Learn to make \"badges\"](https://shields.io/) | Example: <img alt=\"Awesome Badge\" src=\"https://img.shields.io/badge/Awesome-😎-blueviolet?style=for-the-badge\"> |

    The version of the OpenAPI document: v1
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from setuptools import (  # noqa: H301
    find_packages,
    setup,
)

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools
NAME = "files-api-sdk"
VERSION = "1.0.0"
PYTHON_REQUIRES = ">=3.7"
REQUIRES = ["urllib3 >= 1.25.3, < 3.0.0", "python-dateutil", "pydantic >= 1.10.5, < 2", "aenum"]

setup(
    name=NAME,
    version=VERSION,
    description="Files API",
    author="OpenAPI Generator community",
    author_email="team@openapitools.org",
    url="",
    keywords=["OpenAPI", "OpenAPI-Generator", "Files API"],
    install_requires=REQUIRES,
    packages=find_packages(exclude=["test", "tests"]),
    include_package_data=True,
    long_description_content_type="text/markdown",
    long_description="""\
    ![Maintained by](https://img.shields.io/badge/Maintained%20by-MLOps%20Club-05998B?style&#x3D;for-the-badge)  | Helpful Links | Notes | | --- | --- | | [Course Homepage](https://mlops-club.org) | | | [Course Student Portal](https://courses.mlops-club.org) | | | [Course Materials Repo](https://github.com/mlops-club/python-on-aws-course.git) | &#x60;mlops-club/python-on-aws-course&#x60; | | [Course Reference Project Repo](https://github.com/mlops-club/cloud-course-project.git) | &#x60;mlops-club/cloud-course-project&#x60; | | [FastAPI Documentation](https://fastapi.tiangolo.com/) | | | [Learn to make \&quot;badges\&quot;](https://shields.io/) | Example: &lt;img alt&#x3D;\&quot;Awesome Badge\&quot; src&#x3D;\&quot;https://img.shields.io/badge/Awesome-😎-blueviolet?style&#x3D;for-the-badge\&quot;&gt; |
    """,  # noqa: E501
    package_data={"files_api_sdk": ["py.typed"]},
)
