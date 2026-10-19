"""Small retrieval adapter around the public notebooklm-py SDK."""

import asyncio
from collections.abc import Callable
from typing import Any

from notebooklm import NotebookLMClient

from .config import Settings


class BackendError(Exception):
    """Safe, fixed messages suitable for an MCP response."""


class Backend:
    def __init__(self, settings: Settings, factory: Callable | None = None):
        self.settings = settings
        self.factory = factory or NotebookLMClient.from_storage
        self.lock = asyncio.Lock()

    async def _rows(self, client) -> list:
        rows = await client.notebooks.list()
        if self.settings.allowed_notebooks:
            rows = [r for r in rows if r.id in self.settings.allowed_notebooks]
        return rows

    async def _resolve(self, client, query: str) -> str:
        query = query.strip()
        if not query:
            raise BackendError("INVALID_NOTEBOOK: Provide a notebook ID or a unique title fragment.")
        query = self.settings.aliases.get(query.casefold(), query)
        rows = await self._rows(client)
        exact = [r for r in rows if r.id == query]
        if len(exact) == 1:
            return exact[0].id
        hits = [r for r in rows if r.id.startswith(query)]
        if not hits:
            hits = [r for r in rows if query.casefold() in r.title.casefold()]
        if len(hits) != 1:
            raise BackendError("NOTEBOOK_NOT_FOUND_OR_AMBIGUOUS: Use list_notebooks and an exact allowed ID.")
        return hits[0].id

    async def call(self, operation: str, **kwargs) -> dict[str, Any]:
        # Serialize calls that share a cookie file; never reuse another caller's credential.
        async with self.lock:
            try:
                async with asyncio.timeout(self.settings.timeout):
                    async with self.factory(
                        path=self.settings.storage, profile=self.settings.profile
                    ) as client:
                        return await self._dispatch(client, operation, **kwargs)
            except BackendError:
                raise
            except TimeoutError:
                raise BackendError(
                    "TIMEOUT: NotebookLM did not respond within the configured time."
                ) from None
            except Exception:
                # SDK exceptions/HTML may contain cookies, tokens, account details or source text.
                raise BackendError(
                    "UPSTREAM_ERROR: NotebookLM could not complete this request. "
                    "Check your local login with 'notebooklm auth check --test' and log in again if needed. "
                    "A failed request does not mean your notebook is empty."
                ) from None

    async def _dispatch(self, client, operation: str, **kwargs) -> dict:
        if operation == "list_notebooks":
            rows = await self._rows(client)
            return {"notebooks": [{"id": r.id, "title": r.title, "is_owner": r.is_owner} for r in rows]}
        notebook_id = await self._resolve(client, kwargs["notebook"])
        result: dict[str, Any] = {"notebook_id": notebook_id}
        if operation == "list_sources":
            rows = await client.sources.list(notebook_id)
            result["sources"] = [{"id": r.id, "title": r.title, "url": r.url} for r in rows]
        elif operation == "source_fulltext":
            source_id = kwargs["source_id"]
            rows = await client.sources.list(notebook_id)
            if source_id not in {r.id for r in rows}:
                raise BackendError("SOURCE_NOT_FOUND: The source is not in the selected notebook.")
            source = await client.sources.get_fulltext(notebook_id, source_id)
            result.update(
                source_id=source.source_id,
                title=source.title,
                text=source.content,
                char_count=len(source.content),
                url=source.url,
            )
        elif operation == "notebook_summary":
            result["summary"] = await client.notebooks.get_summary(notebook_id)
        elif operation == "ask":
            question = kwargs["question"].strip()
            if not question or len(question) > 20000:
                raise BackendError("INVALID_QUESTION: Supply between 1 and 20000 characters.")
            answer = await client.chat.ask(notebook_id, question)
            result.update(
                answer=answer.answer,
                conversation_id=answer.conversation_id,
                references=[
                    {
                        "citation_number": r.citation_number,
                        "source_id": r.source_id,
                        "cited_text": r.cited_text,
                    }
                    for r in answer.references
                ],
            )
        else:
            raise BackendError("UNKNOWN_OPERATION")
        return result
