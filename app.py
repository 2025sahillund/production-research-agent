"""
Production-Grade AI Research Agent - Streamlit Interactive UI.
Visualizes agentic decomposition, resilient tool calling, structured outputs,
and independent judge audits.
"""

import streamlit as st
import json
import time
import os
from src.agent.orchestrator import ResearchAgent
from src.llm.provider import OpenAIProvider, GeminiProvider, GroqProvider, MockResearchLLM
from src.config import settings

st.set_page_config(
    page_title="Production AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header & Introduction
st.title("🔬 Production AI Research Agent")
st.caption("Engineered for Deep Technical Synthesis, Tool Orchestration, and Verified Grounding")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ System Configuration")
    
    provider_choice = st.selectbox(
        "LLM Provider Engine",
        options=["Deterministic Engine (Local / Zero-Cost)", "OpenAI (GPT-4o)", "Gemini (1.5 Flash)", "Groq (Llama-3.1)"],
        index=0,
        help="Select model backend. The local engine provides deterministic reproducibility without requiring external API keys."
    )
    
    api_key = ""
    llm_instance = None
    
    if "OpenAI" in provider_choice:
        api_key = st.text_input("OpenAI API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
        if api_key:
            llm_instance = OpenAIProvider(api_key=api_key)
    elif "Gemini" in provider_choice:
        api_key = st.text_input("Gemini API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
        if api_key:
            llm_instance = GeminiProvider(api_key=api_key)
    elif "Groq" in provider_choice:
        api_key = st.text_input("Groq API Key", type="password", value=os.getenv("GROQ_API_KEY", ""))
        if api_key:
            llm_instance = GroqProvider(api_key=api_key)
    
    if not llm_instance:
        llm_instance = MockResearchLLM()

    st.divider()
    st.markdown("### 🛡️ Production Guardrails")
    st.checkbox("Prompt Injection Defenses", value=True, disabled=True)
    st.checkbox("Deterministic Schema Validation", value=True, disabled=True)
    st.checkbox("Independent Judge Verification", value=True, disabled=True)
    st.checkbox("Automatic Fallback on 404/Timeout", value=True, disabled=True)

    st.divider()
    st.markdown("### 💡 Quick Presets (Assignment Queries)")
    preset = st.radio(
        "Load Example Query:",
        options=[
            "Custom Query",
            "Vector Databases: Qdrant vs Chroma vs Milvus",
            "Indian B2B SaaS: HR Tech Startups",
            "Multi-Agent Architecture: Customer Support Tradeoffs",
            "AI Agent Memory: Comparative Approaches"
        ]
    )

preset_map = {
    "Vector Databases: Qdrant vs Chroma vs Milvus": "Compare the top 3 open-source vector databases for a startup building RAG products.",
    "Indian B2B SaaS: HR Tech Startups": "Find 5 Indian B2B SaaS startups in HR tech and summarize their positioning.",
    "Multi-Agent Architecture: Customer Support Tradeoffs": "Research the pros and cons of using a multi-agent architecture for customer support automation.",
    "AI Agent Memory: Comparative Approaches": "Compare different approaches to adding memory in an AI support agent."
}

default_query = preset_map.get(preset, "")

# Main Query Input
user_query = st.text_area(
    "Enter your technical research question:",
    value=default_query if preset != "Custom Query" else "",
    placeholder="e.g. Compare the top 3 open-source vector databases for a startup building RAG products...",
    height=90
)

col_run, col_clear = st.columns([1, 5])
with col_run:
    run_btn = st.button("🚀 Run Research Agent", type="primary", use_container_width=True)

if run_btn:
    if not user_query.strip():
        st.warning("Please enter a research question first.")
    else:
        agent = ResearchAgent(llm=llm_instance)
        
        with st.status("Agent workflow in progress...", expanded=True) as status:
            st.write("📋 Step 1: Formulating research plan and identifying tool dependencies...")
            time.sleep(0.3)
            
            trace = agent.run(user_query)
            
            st.write(f"🛠️ Step 2: Executed {len(trace.tool_executions)} tool calls (Filtering noise & verifying claims)...")
            st.write("🔬 Step 3: Synthesizing structured report with grounded citations...")
            st.write("⚖️ Step 4: Independent Judge Step auditing factual consistency and hallucination risk...")
            
            status.update(label=f"✅ Research completed in {trace.duration_ms} ms", state="complete", expanded=False)

        # Tabbed Visual Display
        tab1, tab2, tab3, tab4 = st.tabs(["📑 Research Report", "📋 Planning & Tools", "⚖️ Judge & Safety Audit", "🔍 Observability Trace"])

        with tab1:
            res = trace.final_response
            st.subheader("💡 Executive Summary")
            st.info(res.short_answer)

            col_f, col_meta = st.columns([2, 1])

            with col_f:
                st.subheader("📋 Key Findings")
                for idx, finding in enumerate(res.key_findings, 1):
                    st.markdown(f"**{idx}.** {finding}")

                st.subheader("📚 Grounded Sources")
                for s in res.sources_used:
                    with st.expander(f"Source [{s.id}] {s.title} (Reliability: {int(s.reliability_score * 100)}%)"):
                        st.markdown(f"**URL:** [{s.url}]({s.url})")
                        st.markdown(f"**Snippet:** {s.snippet}")

            with col_meta:
                st.subheader("🎯 Confidence & Rigor")
                conf_color = "green" if res.confidence_level == "High" else "orange" if res.confidence_level == "Medium" else "red"
                st.markdown(f"**Level:** :{conf_color}[{res.confidence_level}] ({int(res.confidence_score * 100)}%)")
                st.progress(res.confidence_score)

                st.subheader("⚠️ Assumptions & Limitations")
                for limit in res.limitations_or_assumptions:
                    st.markdown(f"- {limit}")

                st.subheader("🚀 Suggested Next Steps")
                for step in res.suggested_next_steps:
                    st.markdown(f"- {step}")

        with tab2:
            st.subheader("🗺️ Decomposed Research Plan")
            if trace.plan:
                st.markdown(f"**Intent Analysis:** {trace.plan.intent_analysis}")
                for s in trace.plan.decomposed_steps:
                    badge = "✅" if s.status == "completed" else "❌" if s.status == "failed" else "⏳"
                    st.markdown(f"{badge} **Step {s.step_id}:** {s.description} `[Tool: {s.tool_needed}]`")
                    st.caption(f"Rationale: {s.rationale} | Arguments: `{s.tool_input}`")

            st.divider()
            st.subheader("🛠️ Tool Execution & Resilience Telemetry")
            for idx, te in enumerate(trace.tool_executions, 1):
                stat_badge = "🟢 SUCCESS" if te.success else "🔴 FAILED"
                cached_badge = "⚡ (Cached)" if te.cached else ""
                sanitized_badge = "🛡️ (Sanitized)" if te.sanitized else ""
                with st.expander(f"{stat_badge} Call #{idx}: {te.tool_name} {cached_badge} {sanitized_badge} - {te.latency_ms}ms"):
                    st.json(te.model_dump())

        with tab3:
            st.subheader("⚖️ Independent Evaluator / Judge Step (Stretch Goal)")
            if trace.judge_evaluation:
                je = trace.judge_evaluation
                col_j1, col_j2, col_j3 = st.columns(3)
                col_j1.metric("Grounding Score", f"{int(je.grounding_score * 100)}%")
                col_j2.metric("Hallucination Risk", je.hallucination_risk)
                col_j3.metric("Completeness Score", f"{int(je.completeness_score * 100)}%")

                st.markdown("#### Audit Observations")
                for item in je.audit_feedback:
                    st.markdown(f"- {item}")
            else:
                st.write("Judge step was not executed.")

        with tab4:
            st.subheader("🔍 Full Trace Telemetry (JSON)")
            st.json(trace.model_dump())
            st.download_button(
                label="📥 Download Trace JSON",
                data=trace.model_dump_json(indent=2),
                file_name=f"research_trace_{trace.trace_id}.json",
                mime="application/json"
            )
