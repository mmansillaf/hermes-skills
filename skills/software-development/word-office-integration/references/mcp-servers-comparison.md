# MCP Servers for Word — Comparative Analysis

Six MCP servers analyzed. None implement an in-Word chat panel — all are headless .docx manipulation.

## Comparison Table

| Server | Stars | Stack | Platform | Tools | Status | Best For |
|--------|-------|-------|----------|-------|--------|----------|
| GongRzhe/Office-Word-MCP-Server | ★1,902 | Python + python-docx | Cross-platform | 50+ | ARCHIVED Mar 2026 | Quick .docx creation/editing |
| PsychQuant/che-word-mcp | ★3 | Swift pure + OOXML | macOS only | 233 | Active v3.13.5 | Byte-perfect round-trip, Track Changes |
| OfficeMCP/OfficeMCP | ★78 | Python + COM | Windows only | Full Office suite | Active v1.0.5 | Windows Office automation |
| ForLegalAI/mcp-ms-office-documents | ★25 | Python + python-docx | Cross-platform | docx/pptx/xlsx/eml | Active | Legal document creation |
| vAirpower/macos-office365-mcp-server | ★13 | Python + AppleScript | macOS only | Word/PowerPoint/Excel | Active PoC | Mac Office control |
| ecator/cs-office-mcp-server | — | C# | Windows | Office files | Active | .NET ecosystem |

## Key Insight

None of these projects implement a chat panel inside Word. They are MCP servers that manipulate .docx files. The chat-in-Word gap is filled by the Hermes Word Add-in (Office.js task pane + local Python backend), which is complementary to MCP servers — use MCP for headless batch operations and the add-in for interactive chat.

## Most Capable: che-word-mcp

- 233 tools, pure Swift, no external dependencies
- Byte-perfect OOXML round-trip (no silent corruption)
- Programmatic Track Changes (insert/delete/move as revision)
- Content Controls, equations, comments, footnotes
- Single binary — no Python/Node.js runtime needed
- macOS only (universal binary x86_64+arm64)

## Most Popular: office-word-mcp-server

- Available on PyPI: `uvx --from office-word-mcp-server word_mcp_server`
- Smithery badge for one-click install
- Docker support
- But ARCHIVED — no maintenance since March 2026

## Windows-Specific: OfficeMCP

- Uses COM interface for full Office control
- Includes WPS Office support
- RunPython tool allows arbitrary Python execution (security risk)
- SSE mode for multi-client support
