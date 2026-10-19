from contextlib import asynccontextmanager
from types import SimpleNamespace as Row
from unittest.mock import AsyncMock

import pytest

from notebooklm_readonly_mcp.backend import Backend, BackendError
from notebooklm_readonly_mcp.config import Settings


@pytest.fixture
def fake():
    notebooks = [
        Row(id="nb-one", title="First notebook", is_owner=True),
        Row(id="nb-two", title="Second notebook", is_owner=True),
    ]
    sources = [
        Row(id="source-b", title="B", url=None),
        Row(id="source-a", title="A", url="https://example.org"),
    ]
    return Row(
        notebooks=Row(list=AsyncMock(return_value=notebooks), get_summary=AsyncMock(return_value="Summary")),
        sources=Row(
            list=AsyncMock(return_value=sources),
            get_fulltext=AsyncMock(
                return_value=Row(source_id="source-a", title="A", content="가나다라" * 2500, url=None)
            ),
        ),
        chat=Row(
            ask=AsyncMock(
                return_value=Row(
                    answer="Answer [7]",
                    conversation_id="conversation",
                    references=[Row(citation_number=7, source_id="source-a", cited_text="Evidence")],
                )
            )
        ),
    )


def backend(fake, settings=None):
    @asynccontextmanager
    async def factory(**kwargs):
        yield fake

    return Backend(settings or Settings(), factory=factory)


async def test_fulltext_preserved(fake):
    result = await backend(fake).call("source_fulltext", notebook="nb-one", source_id="source-a")
    assert result["char_count"] == 10000
    assert result["text"] == "가나다라" * 2500


async def test_reference_uses_actual_citation_number(fake):
    result = await backend(fake).call("ask", notebook="First", question="What?")
    assert result["references"] == [{"citation_number": 7, "source_id": "source-a", "cited_text": "Evidence"}]


async def test_allowlist_enforced_for_every_tool(fake):
    instance = backend(fake, Settings(allowed_notebooks=frozenset({"nb-one"})))
    assert len((await instance.call("list_notebooks"))["notebooks"]) == 1
    for operation, params in [
        ("list_sources", {}),
        ("source_fulltext", {"source_id": "source-a"}),
        ("notebook_summary", {}),
        ("ask", {"question": "test"}),
    ]:
        with pytest.raises(BackendError, match="NOTEBOOK_NOT_FOUND"):
            await instance.call(operation, notebook="nb-two", **params)
    fake.sources.list.assert_not_called()
    fake.chat.ask.assert_not_called()


async def test_alias_and_ambiguous_query(fake):
    instance = backend(fake, Settings(aliases={"favorite": "nb-one"}))
    assert (await instance.call("notebook_summary", notebook=" FAVORITE "))["summary"] == "Summary"
    with pytest.raises(BackendError, match="AMBIGUOUS"):
        await instance.call("list_sources", notebook="notebook")


async def test_failed_auth_never_becomes_empty_list_or_leaks_exception(fake):
    fake.notebooks.list.side_effect = RuntimeError("secret-value user@example.org Cookie: sensitive")
    with pytest.raises(BackendError, match="UPSTREAM_ERROR") as caught:
        await backend(fake).call("list_notebooks")
    assert "secret-value" not in str(caught.value)
    assert "user@example.org" not in str(caught.value)


async def test_real_empty_list_is_success(fake):
    fake.notebooks.list.return_value = []
    assert await backend(fake).call("list_notebooks") == {"notebooks": []}


async def test_unknown_source_rejected_before_retrieval(fake):
    with pytest.raises(BackendError, match="SOURCE_NOT_FOUND"):
        await backend(fake).call("source_fulltext", notebook="nb-one", source_id="another-notebook-source")
    fake.sources.get_fulltext.assert_not_called()


@pytest.mark.parametrize("question", [" ", "x" * 20001])
async def test_invalid_question_not_sent(fake, question):
    with pytest.raises(BackendError, match="INVALID_QUESTION"):
        await backend(fake).call("ask", notebook="nb-one", question=question)
    fake.chat.ask.assert_not_called()
