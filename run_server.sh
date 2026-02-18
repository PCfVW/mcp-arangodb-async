#!/bin/bash
cd /home/claude/projects/mcp-arango-mind/mcp-arangodb-async
exec .venv/bin/python -m mcp_arangodb_async.entry "$@"
