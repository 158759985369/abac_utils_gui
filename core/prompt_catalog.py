from __future__ import annotations

import re


class PromptCatalog:
    INIT_FORCE_CONFIRM = re.escape(
        "Are you sure you want to overwrite existing config ? It will remove all the existing ABAC attributes and rules [Y/N] ? "
    )
    AVP_NEW_NAME = re.escape("Enter new attribute name: ")
    AVP_NEW_VALUES = re.escape("Enter comma(',') values: ")
    AVP_MODIFY_NAME = re.escape("Name of the attribute to modify: ")
    AVP_MODIFY_VALUES = re.escape("Enter new comma(',') values: ")
    AVP_DELETE_NAME = re.escape("Name of the attribute-value pair to delete: ")

    USER_ATTRIBUTE_VALUE = re.escape("value: ")
    USER_PASSWORD = re.escape("Password: ")
    USER_PASSWORD_CONFIRM = re.escape("Re-enter Password: ")

    POLICY_ATTRIBUTE_VALUE_PREFIX = "Select the value for attribute  - "
    POLICY_OPERATION = re.escape("Operation: Modify [M] or Read [R]: ")
    POLICY_DELETE_INDEX = re.escape("Index of the rule to delete: ")

    OBJ_NEW_ATTRIBUTE_PREFIX = "Select new attribute from - "
    OBJ_NEW_VALUE_PREFIX = "Select new value - "
    OBJ_CHANGE_ATTRIBUTE_PREFIX = "Select attribute to change - "
    OBJ_CHANGE_VALUE_PREFIX = "Select new value for attribute - "
    OBJ_DELETE_ATTRIBUTE_PREFIX = "Select attribute to delete - "

    @staticmethod
    def exact(text: str) -> str:
        return re.escape(text)

    @staticmethod
    def policy_attr_prompt(name: str, values: list[str]) -> str:
        return re.escape(
            f"Select the value for attribute  - {name} from [{', '.join(values)}] : "
        )

    @staticmethod
    def obj_add_name_prompt(valid_names: list[str]) -> str:
        return re.escape(f"Select new attribute from - {', '.join(valid_names)}: ")

    @staticmethod
    def obj_add_value_prompt(name: str, values: list[str]) -> str:
        return re.escape(f"Select new value - {name} from [{', '.join(values)}]: ")

    @staticmethod
    def obj_change_name_prompt(valid_names: list[str]) -> str:
        return re.escape(f"Select attribute to change - {', '.join(valid_names)}: ")

    @staticmethod
    def obj_change_value_prompt(name: str, values: list[str]) -> str:
        return re.escape(f"Select new value for attribute - {name} from [{', '.join(values)}]: ")

    @staticmethod
    def obj_delete_name_prompt(valid_names: list[str]) -> str:
        return re.escape(f"Select attribute to delete - {', '.join(valid_names)}: ")
