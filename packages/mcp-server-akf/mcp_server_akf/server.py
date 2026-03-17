"""MCP server implementation for AKF — Agent Knowledge Format.

Exposes 9 tools via Model Context Protocol:
  - create_claim: Create AKF trust metadata
  - validate_file: Validate an .akf file
  - scan_file: Security scan any file
  - trust_score: Compute effective trust score
  - stamp_file: Stamp trust metadata onto any file
  - audit_file: Run compliance audit
  - embed_file: Embed AKF metadata into any format
  - extract_file: Extract AKF metadata from any format
  - detect_threats: Run security detections
"""

from __future__ import annotations

import asyncio
import json
import sys

import akf
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def create_claim(content: str, confidence: float, source: str | None = None, ai_generated: bool = True) -> dict:
    """Create an AKF claim and return as JSON."""
    unit = akf.create(
        content,
        confidence=confidence,
        source=source or "mcp-tool",
        ai_generated=ai_generated,
    )
    return unit.to_dict()


def validate_file(path: str) -> dict:
    """Validate an .akf file."""
    result = akf.validate(path)
    return {
        "valid": result.valid,
        "level": result.level,
        "errors": result.errors,
        "warnings": result.warnings,
    }


def scan_file(path: str) -> dict:
    """Security scan any file for AKF metadata."""
    from akf import universal
    report = universal.scan(path)
    return {
        "enriched": report.enriched,
        "format": report.format,
        "claim_count": report.claim_count,
        "classification": report.classification,
        "overall_trust": report.overall_trust,
        "ai_contribution": report.ai_contribution,
    }


def trust_score(content: str, confidence: float, authority_tier: int = 3) -> dict:
    """Compute effective trust score for a claim."""
    from akf.models import Claim
    from akf.trust import effective_trust

    claim = Claim(content=content, confidence=confidence, authority_tier=authority_tier)
    result = effective_trust(claim)
    return {
        "score": result.score,
        "decision": result.decision,
        "breakdown": result.breakdown,
    }


def stamp_file(path: str, agent: str = "mcp-agent", classification: str = "internal",
               confidence: float = 0.85, evidence: str | None = None) -> dict:
    """Stamp trust metadata onto any file."""
    from akf.stamp import stamp_file as _stamp

    evidence_list = [e.strip() for e in evidence.split(",")] if evidence else []
    result = _stamp(
        path,
        agent=agent,
        classification=classification,
        trust_score=confidence,
        evidence=evidence_list,
    )
    return {"stamped": True, "path": str(path), "agent": agent, "classification": classification}


def audit_file(path: str, regulation: str | None = None) -> dict:
    """Run compliance audit on an AKF file."""
    result = akf.audit(path, regulation=regulation)
    return {
        "compliant": result.compliant,
        "regulation": regulation or "general",
        "score": getattr(result, "score", None),
        "findings": [str(f) for f in getattr(result, "findings", [])],
        "recommendations": getattr(result, "recommendations", []),
    }


def embed_file(path: str, content: str, confidence: float = 0.85,
               source: str | None = None, classification: str = "internal") -> dict:
    """Embed AKF metadata into any supported file format."""
    from akf import universal

    claim_dict = {"c": content, "t": confidence}
    if source:
        claim_dict["src"] = source
    universal.embed(path, claims=[claim_dict], classification=classification)
    return {"embedded": True, "path": str(path), "format": path.rsplit(".", 1)[-1]}


def extract_file(path: str) -> dict:
    """Extract AKF metadata from any supported file format."""
    from akf import universal

    meta = universal.extract(path)
    if meta is None:
        return {"found": False, "path": str(path)}
    return {"found": True, "path": str(path), "metadata": meta}


def detect_threats(path: str) -> dict:
    """Run security detections on an AKF file."""
    unit = akf.load(path)
    from akf.detection import run_all_detections
    report = run_all_detections(unit)
    return {
        "path": str(path),
        "triggered_count": report.triggered_count,
        "critical_count": report.critical_count,
        "high_count": report.high_count,
        "clean": report.clean,
        "results": [
            {
                "detection": r.detection_class,
                "triggered": r.triggered,
                "severity": r.severity,
                "findings": r.findings,
                "recommendation": r.recommendation,
            }
            for r in report.results
            if r.triggered
        ],
    }


# ---------------------------------------------------------------------------
# MCP tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    Tool(
        name="create_claim",
        description="Create an AKF claim with trust metadata. Returns a JSON object with the claim, trust score, and provenance.",
        inputSchema={
            "type": "object",
            "required": ["content", "confidence"],
            "properties": {
                "content": {"type": "string", "description": "The factual claim to create"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Trust score 0.0-1.0"},
                "source": {"type": "string", "description": "Information source (e.g., 'SEC 10-Q')"},
                "ai_generated": {"type": "boolean", "default": True, "description": "Whether this claim is AI-generated"},
            },
        },
    ),
    Tool(
        name="validate_file",
        description="Validate an .akf file against the AKF specification. Returns validity status, validation level (0-3), errors, and warnings.",
        inputSchema={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string", "description": "Path to the .akf file to validate"},
            },
        },
    ),
    Tool(
        name="scan_file",
        description="Security scan any file for AKF trust metadata. Works with .akf, .docx, .pdf, .html, .md, .json, images, and any format with a sidecar.",
        inputSchema={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string", "description": "Path to the file to scan"},
            },
        },
    ),
    Tool(
        name="trust_score",
        description="Compute the effective trust score for a claim using AKF's trust computation engine. Factors in confidence, authority tier, and temporal decay.",
        inputSchema={
            "type": "object",
            "required": ["content", "confidence"],
            "properties": {
                "content": {"type": "string", "description": "The claim to score"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "description": "Base confidence score"},
                "authority_tier": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3, "description": "Authority tier 1-5 (1=official records, 5=AI inference)"},
            },
        },
    ),
    Tool(
        name="stamp_file",
        description="Stamp AKF trust metadata onto any file. Supports DOCX, PDF, images, Markdown, code, and 20+ formats. Use this after creating or modifying files.",
        inputSchema={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string", "description": "Path to the file to stamp"},
                "agent": {"type": "string", "default": "mcp-agent", "description": "Agent identity (e.g., 'claude-code', 'copilot')"},
                "classification": {"type": "string", "default": "internal", "description": "Security classification: public, internal, confidential, restricted"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.85, "description": "Confidence score"},
                "evidence": {"type": "string", "description": "Comma-separated evidence (e.g., 'tests pass, docs reviewed')"},
            },
        },
    ),
    Tool(
        name="audit_file",
        description="Run compliance audit on an AKF file against regulatory frameworks (EU AI Act, SOX, HIPAA, GDPR, NIST AI RMF, ISO 42001).",
        inputSchema={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string", "description": "Path to the .akf file to audit"},
                "regulation": {"type": "string", "description": "Target regulation: eu_ai_act, sox, hipaa, gdpr, nist_ai, iso_42001"},
            },
        },
    ),
    Tool(
        name="embed_file",
        description="Embed AKF trust metadata into any supported file format (DOCX, PDF, HTML, images, Markdown, etc.).",
        inputSchema={
            "type": "object",
            "required": ["path", "content"],
            "properties": {
                "path": {"type": "string", "description": "Path to the file to embed metadata into"},
                "content": {"type": "string", "description": "The factual claim to embed"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.85, "description": "Confidence score"},
                "source": {"type": "string", "description": "Information source"},
                "classification": {"type": "string", "default": "internal", "description": "Security classification"},
            },
        },
    ),
    Tool(
        name="extract_file",
        description="Extract AKF trust metadata from any supported file format. Returns claims, classification, provenance, and trust scores.",
        inputSchema={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string", "description": "Path to the file to extract metadata from"},
            },
        },
    ),
    Tool(
        name="detect_threats",
        description="Run 10 AI-specific security detections on an AKF file: hallucination risk, knowledge laundering, classification downgrade, trust degradation, and more.",
        inputSchema={
            "type": "object",
            "required": ["path"],
            "properties": {
                "path": {"type": "string", "description": "Path to the .akf file to analyze"},
            },
        },
    ),
]

# Map tool names to handler functions
HANDLERS = {
    "create_claim": create_claim,
    "validate_file": validate_file,
    "scan_file": scan_file,
    "trust_score": trust_score,
    "stamp_file": stamp_file,
    "audit_file": audit_file,
    "embed_file": embed_file,
    "extract_file": extract_file,
    "detect_threats": detect_threats,
}


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("akf")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        handler = HANDLERS.get(name)
        if not handler:
            return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

        try:
            result = handler(**arguments)
            return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    return server


async def run_server():
    """Run the MCP server over stdio."""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point for the MCP server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
