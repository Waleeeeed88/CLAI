import json

from agents.base import AgentResponse, BaseAgent, Message, MessageRole
from config import clear_settings_cache
from config.settings import OVERRIDES_COST_SAVING_KEY


class DummyAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        self.seen_messages = []
        super().__init__(*args, **kwargs)

    @property
    def provider_name(self) -> str:
        return "dummy"

    def _initialize_client(self) -> None:
        self._client = object()

    def _send_request(self, messages):
        self.seen_messages = messages
        return AgentResponse(
            content="ok",
            model=self.model,
            provider=self.provider_name,
            finish_reason="stop",
        )


def _use_tmp_overrides(monkeypatch, tmp_path, payload):
    path = tmp_path / "overrides.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr("config.settings.OVERRIDES_FILE", path)
    clear_settings_cache()
    return path


def test_cost_saver_injects_prompt_and_caps_output(monkeypatch, tmp_path):
    _use_tmp_overrides(
        monkeypatch,
        tmp_path,
        {
            OVERRIDES_COST_SAVING_KEY: {
                "cost_saver_enabled": True,
                "cost_saver_max_output_tokens": 512,
            }
        },
    )

    agent = DummyAgent(model="test-model", system_prompt="Base prompt", max_tokens=4096)

    assert "Cost Saver Mode" in agent.system_prompt
    assert "Ponytail ladder" in agent.system_prompt
    assert "Caveman brevity" in agent.system_prompt
    assert agent.max_tokens == 512


def test_cost_saver_trims_and_compacts_history(monkeypatch, tmp_path):
    _use_tmp_overrides(
        monkeypatch,
        tmp_path,
        {
            OVERRIDES_COST_SAVING_KEY: {
                "cost_saver_enabled": True,
                "cost_saver_history_messages": 2,
                "cost_saver_history_char_limit": 20,
            }
        },
    )

    agent = DummyAgent(model="test-model")
    agent.conversation_history = [
        Message(MessageRole.USER, "old user"),
        Message(MessageRole.ASSISTANT, "old assistant"),
        Message(MessageRole.USER, "recent user " + ("x" * 40)),
        Message(MessageRole.ASSISTANT, "recent assistant " + ("y" * 40)),
    ]

    agent.chat("current", include_history=True)

    assert [message.role for message in agent.seen_messages] == [
        MessageRole.USER,
        MessageRole.ASSISTANT,
        MessageRole.USER,
    ]
    assert agent.seen_messages[-1].content == "current"
    assert "old user" not in [message.content for message in agent.seen_messages]
    assert len(agent.seen_messages[0].content) <= 27
