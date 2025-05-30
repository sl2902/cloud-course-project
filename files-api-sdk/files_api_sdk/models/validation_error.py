# coding: utf-8

"""
    Files API

    ![Maintained by](https://img.shields.io/badge/Maintained%20by-MLOps%20Club-05998B?style=for-the-badge)  | Helpful Links | Notes | | --- | --- | | [Course Homepage](https://mlops-club.org) | | | [Course Student Portal](https://courses.mlops-club.org) | | | [Course Materials Repo](https://github.com/mlops-club/python-on-aws-course.git) | `mlops-club/python-on-aws-course` | | [Course Reference Project Repo](https://github.com/mlops-club/cloud-course-project.git) | `mlops-club/cloud-course-project` | | [FastAPI Documentation](https://fastapi.tiangolo.com/) | | | [Learn to make \"badges\"](https://shields.io/) | Example: <img alt=\"Awesome Badge\" src=\"https://img.shields.io/badge/Awesome-😎-blueviolet?style=for-the-badge\"> |

    The version of the OpenAPI document: v1
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations

import json
import pprint
import re  # noqa: F401

from files_api_sdk.models.validation_error_loc_inner import ValidationErrorLocInner
from pydantic import (
    BaseModel,
    Field,
    StrictStr,
    conlist,
)


class ValidationError(BaseModel):
    """
    ValidationError
    """

    loc: conlist(ValidationErrorLocInner) = Field(...)
    msg: StrictStr = Field(...)
    type: StrictStr = Field(...)
    __properties = ["loc", "msg", "type"]

    class Config:
        """Pydantic configuration"""

        allow_population_by_field_name = True
        validate_assignment = True

    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.dict(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> ValidationError:
        """Create an instance of ValidationError from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.dict(by_alias=True, exclude={}, exclude_none=True)
        # override the default output from pydantic by calling `to_dict()` of each item in loc (list)
        _items = []
        if self.loc:
            for _item in self.loc:
                if _item:
                    _items.append(_item.to_dict())
            _dict["loc"] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> ValidationError:
        """Create an instance of ValidationError from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return ValidationError.parse_obj(obj)

        _obj = ValidationError.parse_obj(
            {
                "loc": [ValidationErrorLocInner.from_dict(_item) for _item in obj.get("loc")]
                if obj.get("loc") is not None
                else None,
                "msg": obj.get("msg"),
                "type": obj.get("type"),
            }
        )
        return _obj
