"""
Script to generate sample research traces.
"""

from src.agent.orchestrator import ResearchAgent

agent = ResearchAgent()

queries = [
    ("Compare the top 3 open-source vector databases for a startup building RAG products.", "samples/sample_1_vectordb.json"),
    ("Find 5 Indian B2B SaaS startups in HR tech and summarize their positioning.", "samples/sample_2_hrtech_saas.json"),
    ("Research the pros and cons of using a multi-agent architecture for customer support automation.", "samples/sample_3_multiagent_support.json")
]

for q, path in queries:
    trace = agent.run(q)
    with open(path, "w", encoding="utf-8") as f:
        f.write(trace.model_dump_json(indent=2))
    print(f"Generated {path}")

