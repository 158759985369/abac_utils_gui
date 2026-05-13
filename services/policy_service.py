from __future__ import annotations

from core.command_session import CommandSession
from core.interactive_runner import InteractiveRunner
from core.session_builder import SessionBuilder
from repositories.avp_repository import AvpRepository
from repositories.policy_repository import PolicyRepository


class PolicyService:
    def __init__(
        self,
        runner: InteractiveRunner,
        builder: SessionBuilder,
        policy_repository: PolicyRepository,
        avp_repository: AvpRepository,
    ) -> None:
        self.runner = runner
        self.builder = builder
        self.policy_repository = policy_repository
        self.avp_repository = avp_repository

    def list_rules(self) -> list[dict[str, object]]:
        return self.policy_repository.list_rules()

    def add(
        self,
        user_selections: dict[str, str],
        obj_selections: dict[str, str],
        env_selections: dict[str, str],
        operation: str,
    ):
        avps = self.avp_repository.load()
        return CommandSession(
            self.builder.build_policy_add(
                avps["user"],
                avps["obj"],
                avps["env"],
                user_selections,
                obj_selections,
                env_selections,
                operation,
            ),
            self.runner,
        ).execute()

    def delete(self, index: int):
        rules = self.policy_repository.list_rules()
        rendered_rule = PolicyRepository.render_rule(rules[index])
        return CommandSession(
            self.builder.build_policy_delete(index, rendered_rule),
            self.runner,
        ).execute()

