"""
Command-Line Interface for the Production AI Research Agent.
Supports interactive mode, single-query execution, and JSON output export.
"""

import argparse
import json
import sys
import logging

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from src.agent.orchestrator import ResearchAgent
from src.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def format_cli_output(trace):
    res = trace.final_response
    print("\n" + "=" * 80)
    print(f"🔬 RESEARCH REPORT: {res.user_question}")
    print("=" * 80)
    print(f"\n💡 SHORT ANSWER:\n{res.short_answer}\n")
    
    print("📋 KEY FINDINGS:")
    for idx, f in enumerate(res.key_findings, 1):
        print(f"  {idx}. {f}")
    
    print("\n📚 SOURCES USED:")
    for s in res.sources_used:
        print(f"  [{s.id}] {s.title} ({s.reliability_score * 100:.0f}% reliability)")
        print(f"      URL: {s.url}")
        print(f"      Snippet: {s.snippet[:120]}...\n")
    
    print(f"🎯 CONFIDENCE: {res.confidence_level} ({res.confidence_score * 100:.1f}%)")
    
    print("\n⚠️ LIMITATIONS & ASSUMPTIONS:")
    for a in res.limitations_or_assumptions:
        print(f"  • {a}")
        
    print("\n🚀 SUGGESTED NEXT STEPS:")
    for n in res.suggested_next_steps:
        print(f"  → {n}")

    if trace.judge_evaluation:
        je = trace.judge_evaluation
        print("\n⚖️ INDEPENDENT JUDGE AUDIT:")
        print(f"  Grounding Score: {je.grounding_score * 100:.1f}% | Hallucination Risk: {je.hallucination_risk} | Complete: {je.completeness_score * 100:.1f}%")
        for fb in je.audit_feedback:
            print(f"    - {fb}")

    print("\n⏱️ TELEMETRY:")
    print(f"  Execution Time: {trace.duration_ms} ms | Tools Called: {len(trace.tool_executions)}")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Production-Oriented AI Research Agent")
    parser.add_argument("--query", "-q", type=str, help="Research question to investigate")
    parser.add_argument("--json", action="store_true", help="Output full execution trace in JSON format")
    args = parser.parse_args()

    agent = ResearchAgent()

    if args.query:
        query = args.query
        trace = agent.run(query)
        if args.json:
            print(trace.model_dump_json(indent=2))
        else:
            format_cli_output(trace)
    else:
        print("\n🤖 Production AI Research Agent (Interactive Mode)")
        print("Type 'exit' or 'quit' to close.\n")
        while True:
            try:
                user_input = input("Research Query > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Exiting...")
                    break
                trace = agent.run(user_input)
                format_cli_output(trace)
            except (KeyboardInterrupt, EOFError):
                print("\nSession terminated.")
                break


if __name__ == "__main__":
    main()
