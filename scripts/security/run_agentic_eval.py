#!/usr/bin/env python3
"""
LangGraph ReAct Security Investigator & STRIDE Threat Modeler.
Uses a stateful LangGraph workflow (`StateGraph`) with Gemini tool-calling so the
LLM autonomously decides what additional repository context to inspect:
  1. `investigate_node`: Analyzes the PR diff and decides which repository tools
     (`list_files`, `search_code`, `read_file`, `inspect_terraform`) to call to verify
     IAM least-privilege, SDK usage, middleware gates, or network reachability.
  2. `tools_node`: Executes the requested repository tools and appends observations
     back into the graph state.
  3. `synthesize_node`: Produces the final, schema-validated Pydantic security report
     grounded in both the diff and the agent's autonomous tool discoveries.
"""
import argparse
import json
import os
import subprocess
import sys
from typing import Any, TypedDict
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END

from repo_tools import make_agent_tools, redact_secrets


class ThreatItem(BaseModel):
    category: str = Field(
        description="STRIDE category: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, or Elevation of Privilege"
    )
    trust_boundary: str = Field(
        description="Trust boundary crossed or impacted by the change in this PR"
    )
    affected_component: str = Field(
        description="Specific file, resource, or route modified in this PR diff"
    )
    description: str = Field(
        description="Concrete architectural or code-level threat introduced or modified by this PR diff"
    )
    raw_severity: str = Field(
        description="Severity before cross-referencing repository context (Critical, High, Medium, Low)"
    )
    contextual_severity: str = Field(
        description="Adjusted severity after autonomous tool investigation of how the rest of the repo's code and infrastructure interact with this change (Critical, High, Medium, Low)"
    )
    context_rationale: str = Field(
        description="How the files/code/infrastructure discovered via tool calls justified downgrading, escalating, or flagging this change"
    )
    ai_agent_prompt: str = Field(
        description=(
            "Copy-pasteable CodeRabbit-style 'Prompt for AI Agents' instructing a coding agent to: "
            "(1) inspect the exact file/lines/functions in `affected_component` and verify the finding against surrounding context, "
            "(2) apply the specific security fix without breaking existing functionality, and "
            "(3) run or add a pytest verification test to confirm the fix."
        )
    )
    suggested_fix: str = Field(
        description="Actionable code or Terraform HCL remediation snippet for the modified file in this PR"
    )


class SecurityReport(BaseModel):
    summary: str = Field(
        description="Executive summary of the security impact of the changes introduced in this pull request"
    )
    context_summary_narrative: str = Field(
        description="2-3 sentence summary explaining what additional repo context was inspected via tools (reachability, IAM scope, middleware, SDK usage) and how the PR changes interact with existing code and infrastructure"
    )
    data_flow_diagram_ascii: str = Field(
        description="Compact ASCII Data Flow Diagram (DFD) illustrating the data flow and trust boundaries of the components modified in this PR"
    )
    overall_contextual_severity: str = Field(
        description="Highest contextual severity remaining across threats introduced in this PR (Critical, High, Medium, Low, or Informational)"
    )
    threats: list[ThreatItem]


class PRSecurityAgentState(TypedDict):
    repo_root: str
    git_diff: str
    materiality_context: dict[str, Any]
    contents: list[Any]
    tool_trace: list[str]
    iterations: int
    max_iterations: int
    pending_tool_calls: list[dict[str, Any]]
    final_report: dict[str, Any]


def get_git_diff(base_ref: str = "origin/main") -> str:
    try:
        cmd = ["git", "diff", f"{base_ref}...HEAD"]
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    except Exception:
        cmd = ["git", "diff", "HEAD~1"]
        return subprocess.check_output(cmd, text=True)


def call_gemini_with_fallback(
    client: genai.Client,
    contents: Any,
    config: types.GenerateContentConfig,
) -> Any:
    primary = os.getenv("GEMINI_SECURITY_MODEL", "gemini-3.5-flash")
    candidates = list(dict.fromkeys([primary, "gemini-2.5-flash", "gemini-2.0-flash"]))
    last_err = None
    for model_name in candidates:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except Exception as err:
            print(f"Warning: Model '{model_name}' failed ({err}), trying next fallback...")
            last_err = err
    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")


def build_pr_security_graph(client: genai.Client, repo_root: str):
    """Builds and compiles the LangGraph ReAct state machine for PR Security Evaluation."""
    tool_bundle = make_agent_tools(repo_root)
    tool_functions = tool_bundle["functions"]
    tool_dispatch = tool_bundle["dispatch"]

    def investigate_node(state: PRSecurityAgentState) -> dict[str, Any]:
        """LLM reasoning node that inspects the diff and decides which repo tools to invoke."""
        contents = list(state["contents"])
        if not contents:
            initial_prompt = f"""
You are an autonomous Principal DevSecOps & Application Security Agent investigating a Pull Request.
You have access to live repository exploration tools:
- `list_files(subdir, glob_pattern)`: Discover directories, modules, or services anywhere in the repo.
- `search_code(regex_query, file_glob)`: Search across all code and Terraform files for SDK calls, IAM roles, routes, middlewares, or secrets.
- `read_file(file_path, start_line, end_line)`: Read any file in the repository to verify implementation details.
- `inspect_terraform(tf_path)`: Parse `.tf` files into structured HCL2 JSON.

HOW TO INVESTIGATE THIS PR:
1. Review the `PULL REQUEST GIT DIFF` and `MODIFIED FILES SUMMARY` below.
2. Autonomously decide what additional context from the repository you need to accurately threat-model the change:
   - **Architecture Decision Records (`docs/adr/*.md`) & Threat Model (`SECURITY.md`)**: If a change touches architectural patterns, authentication/WIF (`ADR-005`), rate limiting (`ADR-007`), serverless Cloud Run scaling (`ADR-001`), vector store (`ADR-004`), or LangGraph/agent workflows (`ADR-009`), use `list_files("docs/adr")` or `read_file` to check whether the design trade-offs or intentional security constraints are already documented in an ADR or `SECURITY.md`.
   - **If an IAM policy, role, or Terraform resource was modified**: use `search_code` or `read_file` to check how the application code actually uses that service/permission (e.g., is the permission needed, or does it violate Least Privilege?).
   - **If an application route, service, or script was modified**: use `search_code`, `read_file`, or `inspect_terraform` to check how it is exposed (ingress, auth middleware, callers) and what runtime permissions it executes under.
3. Call only the tools you need (typically 1 to 4 targeted tool calls). Once you have sufficient evidence, stop calling tools and summarize your findings.

MODIFIED FILES SUMMARY:
{json.dumps(state['materiality_context'], indent=2)}

PULL REQUEST GIT DIFF:
```diff
{state['git_diff'][:18000]}
```
"""
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=initial_prompt)]))

        response = call_gemini_with_fallback(
            client=client,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=tool_functions,
                temperature=0.1,
            ),
        )

        candidate_content = response.candidates[0].content
        contents.append(candidate_content)

        calls = []
        if response.function_calls:
            for fc in response.function_calls:
                calls.append({"name": fc.name, "args": dict(fc.args) if fc.args else {}})

        return {
            "contents": contents,
            "pending_tool_calls": calls,
            "iterations": state["iterations"] + 1,
        }

    def tools_node(state: PRSecurityAgentState) -> dict[str, Any]:
        """Executes every tool call requested by Gemini and feeds results back into graph state."""
        contents = list(state["contents"])
        trace = list(state["tool_trace"])
        response_parts = []

        for call in state.get("pending_tool_calls", []):
            fn_name = call["name"]
            fn_args = call["args"]
            trace_entry = f"{fn_name}({json.dumps(fn_args)})"
            print(f"[LangGraph Tool Call] {trace_entry}")
            trace.append(trace_entry)

            fn = tool_dispatch.get(fn_name)
            if fn is None:
                result_str = f"Error: Unknown tool '{fn_name}'."
            else:
                try:
                    result_str = fn(**fn_args)
                except Exception as e:
                    result_str = f"Error executing {fn_name}: {e}"

            response_parts.append(
                types.Part.from_function_response(
                    name=fn_name,
                    response={"result": result_str},
                )
            )

        contents.append(types.Content(role="tool", parts=response_parts))
        return {
            "contents": contents,
            "tool_trace": trace,
            "pending_tool_calls": [],
        }

    def synthesize_node(state: PRSecurityAgentState) -> dict[str, Any]:
        """Final node that synthesizes all tool observations and the PR diff into a structured SecurityReport."""
        contents = list(state["contents"])
        synthesis_prompt = """
Based on the Pull Request diff and all repository evidence gathered during your tool-calling investigation:
1. Produce the final structured `SecurityReport` JSON.
2. CRITICAL SCOPE RULE: Every `ThreatItem.affected_component` MUST be a file, resource, or route modified in this PR diff. Do not report unrelated backlog issues on untouched files.
3. Use the evidence you gathered from the repository (via `search_code`, `read_file`, `inspect_terraform`, `list_files`, and any relevant ADRs in `docs/adr/` or `SECURITY.md`) to:
   - Verify whether IAM/Terraform changes are actually needed by the code (flagging over-privileged additions as Elevation of Privilege).
   - Verify whether the change aligns with or violates architectural decisions in `docs/adr/*.md` (citing the specific ADR when relevant).
   - Calibrate `raw_severity` -> `contextual_severity` based on actual reachability, middleware protection, documented ADR constraints, and execution environment.
   - Explicitly mention what repo context (and any ADR) was verified in `context_summary_narrative` and `context_rationale`.
4. For every `ThreatItem`, populate `ai_agent_prompt` with a self-contained, copy-pasteable prompt formatted like CodeRabbit's "Prompt for AI Agents":
   - Start with: `In @<file_path> (around <function/resource/lines>), ...`
   - Instruct the coding agent to first **verify the finding** by inspecting the target file and related callers/configs to confirm whether the risk applies.
   - Specify the exact architectural or code modification needed to remediate the issue safely.
   - Instruct the coding agent to run or add a `pytest` test to verify the fix.
"""
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=synthesis_prompt)]))

        response = call_gemini_with_fallback(
            client=client,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SecurityReport,
                temperature=0.1,
            ),
        )
        parsed = json.loads(response.text)
        parsed["agent_tool_trace"] = state.get("tool_trace", [])
        return {"final_report": parsed}

    def should_continue(state: PRSecurityAgentState) -> str:
        if state.get("pending_tool_calls") and state["iterations"] < state["max_iterations"]:
            return "tools"
        return "synthesize"

    workflow = StateGraph(PRSecurityAgentState)
    workflow.add_node("investigate", investigate_node)
    workflow.add_node("tools", tools_node)
    workflow.add_node("synthesize", synthesize_node)

    workflow.set_entry_point("investigate")
    workflow.add_conditional_edges(
        "investigate",
        should_continue,
        {
            "tools": "tools",
            "synthesize": "synthesize",
        },
    )
    workflow.add_edge("tools", "investigate")
    workflow.add_edge("synthesize", END)

    return workflow.compile()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--materiality-file", default="/tmp/materiality_gate.json")
    parser.add_argument("--output-report", default="/tmp/security_report.json")
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--max-iterations", type=int, default=4)
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable is required.", file=sys.stderr)
        sys.exit(1)

    materiality_context = {}
    if args.materiality_file and os.path.exists(args.materiality_file):
        try:
            with open(args.materiality_file, "r", encoding="utf-8") as fh:
                materiality_context = json.load(fh)
        except Exception:
            pass

    git_diff = get_git_diff(args.base_ref)
    if not git_diff.strip():
        print("Empty git diff. Exiting.")
        sys.exit(0)

    client = genai.Client(api_key=api_key)
    graph = build_pr_security_graph(client, args.repo_root)

    initial_state: PRSecurityAgentState = {
        "repo_root": args.repo_root,
        "git_diff": git_diff,
        "materiality_context": materiality_context,
        "contents": [],
        "tool_trace": [],
        "iterations": 0,
        "max_iterations": args.max_iterations,
        "pending_tool_calls": [],
        "final_report": {},
    }

    final_state = graph.invoke(initial_state)
    report = json.loads(redact_secrets(json.dumps(final_state["final_report"])))

    with open(args.output_report, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    print(
        f"Report generated successfully at {args.output_report} "
        f"(Autonomous tool calls executed: {len(report.get('agent_tool_trace', []))})"
    )


if __name__ == "__main__":
    main()
