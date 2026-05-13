from __future__ import annotations

from dataclasses import dataclass

from core.prompt_catalog import PromptCatalog
from core.session_spec import SessionSpec, SessionStep
from repositories.policy_repository import PolicyRepository


@dataclass(slots=True)
class SessionBuilder:
    default_timeout: int = 20

    def build_init(self, force: bool) -> SessionSpec:
        command = ["abac", "init"]
        steps: list[SessionStep] = []
        name = "abac-init"
        if force:
            command.append("--force")
            name = "abac-init-force"
            steps.append(
                SessionStep(
                    phase="CONFIRM_OVERWRITE",
                    prompt_pattern=PromptCatalog.INIT_FORCE_CONFIRM,
                    prompt_label="overwrite-confirm",
                    response="y",
                    recorded_response="y",
                )
            )
        return SessionSpec(name=name, command=command, steps=steps, timeout=self.default_timeout)

    def build_avp_add(self, entity_type: str, name: str, values_csv: str) -> SessionSpec:
        return SessionSpec(
            name=f"avp-{entity_type}-add",
            command=["abac", "avp", "-t", entity_type, "add"],
            steps=[
                SessionStep("ATTRIBUTE_NAME", PromptCatalog.AVP_NEW_NAME, "attribute-name", name),
                SessionStep("ATTRIBUTE_VALUES", PromptCatalog.AVP_NEW_VALUES, "attribute-values", values_csv),
            ],
            timeout=self.default_timeout,
        )

    def build_avp_modify(self, entity_type: str, name: str, values_csv: str) -> SessionSpec:
        return SessionSpec(
            name=f"avp-{entity_type}-modify",
            command=["abac", "avp", "-t", entity_type, "modify"],
            steps=[
                SessionStep("ATTRIBUTE_NAME", PromptCatalog.AVP_MODIFY_NAME, "attribute-name", name),
                SessionStep("ATTRIBUTE_VALUES", PromptCatalog.AVP_MODIFY_VALUES, "attribute-values", values_csv),
            ],
            timeout=self.default_timeout,
        )

    def build_avp_delete(self, entity_type: str, name: str) -> SessionSpec:
        return SessionSpec(
            name=f"avp-{entity_type}-delete",
            command=["abac", "avp", "-t", entity_type, "delete"],
            steps=[
                SessionStep("ATTRIBUTE_NAME", PromptCatalog.AVP_DELETE_NAME, "attribute-name", name),
            ],
            timeout=self.default_timeout,
        )

    def build_user_add(
        self,
        username: str,
        available_avps: dict[str, list[str]],
        selections: dict[str, str],
        password: str,
    ) -> SessionSpec:
        steps: list[SessionStep] = []
        for name in available_avps:
            steps.append(
                SessionStep(
                    phase="USER_ATTR_SECTION",
                    prompt_pattern=PromptCatalog.USER_ATTRIBUTE_VALUE,
                    prompt_label=f"user-attr-{name}",
                    response=selections.get(name, ""),
                    recorded_response=selections.get(name, "<skip>") or "<skip>",
                )
            )
        steps.extend(
            [
                SessionStep(
                    phase="PASSWORD_SECTION",
                    prompt_pattern=PromptCatalog.USER_PASSWORD,
                    prompt_label="password",
                    response=password,
                    sensitive=True,
                ),
                SessionStep(
                    phase="PASSWORD_CONFIRM_SECTION",
                    prompt_pattern=PromptCatalog.USER_PASSWORD_CONFIRM,
                    prompt_label="password-confirm",
                    response=password,
                    sensitive=True,
                ),
            ]
        )
        return SessionSpec(
            name=f"user-add-{username}",
            command=["abac", "user", "add", username],
            steps=steps,
            timeout=self.default_timeout,
        )

    def build_user_delete(self, username: str) -> SessionSpec:
        return SessionSpec(
            name=f"user-delete-{username}",
            command=["abac", "user", "delete", username],
            steps=[
                SessionStep(
                    phase="CONFIRM_DELETE",
                    prompt_pattern=PromptCatalog.exact(
                        f"Are you sure you want to remove user {username} from the system? [Y/N] "
                    ),
                    prompt_label="delete-confirm",
                    response="y",
                    recorded_response="y",
                )
            ],
            timeout=self.default_timeout,
        )

    def build_object_add(
        self,
        object_path: str,
        available_avps: dict[str, list[str]],
        current_avps: dict[str, str],
        attr_name: str,
        value: str,
    ) -> SessionSpec:
        valid_names = [name for name in available_avps if name not in current_avps]
        return SessionSpec(
            name="object-add-attribute",
            command=["abac", "obj", "add", object_path],
            steps=[
                SessionStep(
                    phase="OBJECT_ATTR_SECTION",
                    prompt_pattern=PromptCatalog.obj_add_name_prompt(valid_names),
                    prompt_label="object-attribute-name",
                    response=attr_name,
                ),
                SessionStep(
                    phase="OBJECT_VALUE_SECTION",
                    prompt_pattern=PromptCatalog.obj_add_value_prompt(attr_name, available_avps[attr_name]),
                    prompt_label="object-attribute-value",
                    response=value,
                ),
            ],
            timeout=self.default_timeout,
        )

    def build_object_change(
        self,
        object_path: str,
        available_avps: dict[str, list[str]],
        current_avps: dict[str, str],
        attr_name: str,
        value: str,
    ) -> SessionSpec:
        valid_names = list(current_avps.keys())
        return SessionSpec(
            name="object-change-attribute",
            command=["abac", "obj", "change", object_path],
            steps=[
                SessionStep(
                    phase="OBJECT_ATTR_SECTION",
                    prompt_pattern=PromptCatalog.obj_change_name_prompt(valid_names),
                    prompt_label="object-attribute-name",
                    response=attr_name,
                ),
                SessionStep(
                    phase="OBJECT_VALUE_SECTION",
                    prompt_pattern=PromptCatalog.obj_change_value_prompt(attr_name, available_avps[attr_name]),
                    prompt_label="object-attribute-value",
                    response=value,
                ),
            ],
            timeout=self.default_timeout,
        )

    def build_object_delete(
        self,
        object_path: str,
        current_avps: dict[str, str],
        attr_name: str,
    ) -> SessionSpec:
        valid_names = list(current_avps.keys())
        return SessionSpec(
            name="object-delete-attribute",
            command=["abac", "obj", "delete", object_path],
            steps=[
                SessionStep(
                    phase="OBJECT_ATTR_SECTION",
                    prompt_pattern=PromptCatalog.obj_delete_name_prompt(valid_names),
                    prompt_label="object-attribute-name",
                    response=attr_name,
                )
            ],
            timeout=self.default_timeout,
        )

    def build_policy_add(
        self,
        available_user_avps: dict[str, list[str]],
        available_obj_avps: dict[str, list[str]],
        available_env_avps: dict[str, list[str]],
        user_selections: dict[str, str],
        obj_selections: dict[str, str],
        env_selections: dict[str, str],
        op: str,
    ) -> SessionSpec:
        steps: list[SessionStep] = []
        steps.extend(self._build_policy_section("USER_SECTION", available_user_avps, user_selections))
        steps.extend(self._build_policy_section("OBJ_SECTION", available_obj_avps, obj_selections))
        steps.extend(self._build_policy_section("ENV_SECTION", available_env_avps, env_selections, allow_empty=True))

        rendered_rule = PolicyRepository.render_rule(
            {
                "user": {k: v for k, v in user_selections.items() if v},
                "obj": {k: v for k, v in obj_selections.items() if v},
                "env": {k: v for k, v in env_selections.items() if v},
                "op": "MODIFY" if op == "M" else "READ",
            }
        )
        steps.extend(
            [
                SessionStep(
                    phase="OP_SECTION",
                    prompt_pattern=PromptCatalog.POLICY_OPERATION,
                    prompt_label="policy-operation",
                    response=op,
                ),
                SessionStep(
                    phase="CONFIRM_SECTION",
                    prompt_pattern=PromptCatalog.exact(
                        "Are you sure you want to add the above rule to the policy? [Y/N] "
                    ),
                    prompt_label="policy-confirm",
                    response="y",
                    recorded_response=f"y ({rendered_rule})",
                ),
            ]
        )
        return SessionSpec(
            name="policy-add",
            command=["abac", "policy", "add"],
            steps=steps,
            timeout=self.default_timeout,
            metadata={"rule_preview": rendered_rule},
        )

    def build_policy_delete(self, index: int, rendered_rule: str) -> SessionSpec:
        return SessionSpec(
            name="policy-delete",
            command=["abac", "policy", "delete"],
            steps=[
                SessionStep(
                    phase="RULE_INDEX_SECTION",
                    prompt_pattern=PromptCatalog.POLICY_DELETE_INDEX,
                    prompt_label="policy-index",
                    response=str(index),
                ),
                SessionStep(
                    phase="CONFIRM_SECTION",
                    prompt_pattern=PromptCatalog.exact(
                        "Are you sure you want to delete the above rule from the policy? [Y/N] "
                    ),
                    prompt_label="policy-confirm",
                    response="y",
                    recorded_response=f"y ({rendered_rule})",
                ),
            ],
            timeout=self.default_timeout,
        )

    def build_load(self) -> SessionSpec:
        return SessionSpec(name="abac-load", command=["abac", "load"], steps=[], timeout=self.default_timeout)

    def build_systemctl(self, action: str, service_name: str) -> SessionSpec:
        return SessionSpec(
            name=f"systemctl-{action}-{service_name}",
            command=["systemctl", action, service_name],
            steps=[],
            timeout=self.default_timeout,
        )

    def _build_policy_section(
        self,
        phase: str,
        available_avps: dict[str, list[str]],
        selections: dict[str, str],
        allow_empty: bool = False,
    ) -> list[SessionStep]:
        steps: list[SessionStep] = []
        if not available_avps:
            return steps

        seen_non_empty = False
        for name, values in available_avps.items():
            response = selections.get(name, "")
            if response:
                seen_non_empty = True
            steps.append(
                SessionStep(
                    phase=phase,
                    prompt_pattern=PromptCatalog.policy_attr_prompt(name, values),
                    prompt_label=f"policy-{phase.lower()}-{name}",
                    response=response,
                    recorded_response=response or "<finish-section>",
                )
            )
            if not response:
                break

        if not seen_non_empty and not allow_empty:
            raise ValueError(f"{phase} requires at least one selected attribute value")
        return steps
