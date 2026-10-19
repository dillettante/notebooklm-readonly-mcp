"""Synthetic stdio server. Never opens a real NotebookLM profile."""

from notebooklm_readonly_mcp.config import Settings
from notebooklm_readonly_mcp.server import create_server


class FixtureBackend:
    async def call(self, operation, **kwargs):
        if operation == "list_notebooks":
            return {"notebooks": [{"id": "sample-notebook", "title": "Sample"}]}
        return {
            "notebook_id": "sample-notebook",
            "source_id": "sample-source",
            "text": "sample content " * 1000,
            "char_count": 15000,
        }


if __name__ == "__main__":
    create_server(Settings(), backend=FixtureBackend()).run(transport="stdio")
