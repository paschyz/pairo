import json

import httpx
import respx

from pairo.domain.context_rule import NO_VERDICT, RuleVerdict
from pairo.infrastructure.llm.factory import create_judge
from pairo.infrastructure.llm.fake import FakeLLMReviewer
from pairo.infrastructure.llm.jev_judge import DECISIONS_URL, JevJudge
from pairo.infrastructure.llm.litellm_reviewer import LiteLLMReviewer
from pairo.infrastructure.llm.rate_limiter import RateLimiter


def _judge() -> JevJudge:
    return JevJudge(
        model="~typesafe/jev-latest", rate_limiter=RateLimiter(rpm=1000), api_key="k"
    )


def _answer(noul: float) -> httpx.Response:
    return httpx.Response(
        200, json={"answers": {"durable_rule": {"type": "noul", "noul": noul}}}
    )


@respx.mock
async def test_sends_a_noul_question_with_the_reply_as_state() -> None:
    route = respx.post(DECISIONS_URL).mock(return_value=_answer(0.92))
    got = await _judge().judge_rule("on utilise pas redis", "Use Redis", "a.py")

    assert got == RuleVerdict(True, 0.92)
    req = route.calls.last.request
    assert req.headers["Authorization"] == "Bearer k"
    body = json.loads(req.content)
    assert body["model"] == "~typesafe/jev-latest"
    assert body["questions"]["durable_rule"]["type"] == "noul"
    assert body["state"] == {
        "file": "a.py",
        "finding": "Use Redis",
        "reason": "on utilise pas redis",
    }


@respx.mock
async def test_low_probability_is_not_persisted() -> None:
    respx.post(DECISIONS_URL).mock(return_value=_answer(0.2))
    got = await _judge().judge_rule("not here", "f", "a.py")
    assert got == RuleVerdict(False, 0.2)


@respx.mock
async def test_http_error_is_no_verdict() -> None:
    respx.post(DECISIONS_URL).mock(return_value=httpx.Response(400, json={}))
    assert await _judge().judge_rule("r", "f", "a.py") == NO_VERDICT


@respx.mock
async def test_unexpected_payload_is_no_verdict() -> None:
    respx.post(DECISIONS_URL).mock(return_value=httpx.Response(200, json={"x": 1}))
    assert await _judge().judge_rule("r", "f", "a.py") == NO_VERDICT


def test_factory_uses_jev_for_an_openrouter_judge_model() -> None:
    judge = create_judge("openrouter", api_key="k", model="~typesafe/jev-latest")
    assert isinstance(judge, JevJudge)


def test_factory_falls_back_to_the_chat_model_without_judge_model() -> None:
    assert isinstance(create_judge("openrouter", api_key="k"), LiteLLMReviewer)
    assert isinstance(create_judge("fake", model="x"), FakeLLMReviewer)
