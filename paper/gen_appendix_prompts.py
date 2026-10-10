#!/usr/bin/env python3
"""Emit paper/iclr/appendix_prompts.tex with the verbatim prompts and tool schema from experiments/prompts.py."""
import json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
import prompts as P
def esc(s):
    return s.replace("\\", "\\textbackslash{}").replace("{", "\\{").replace("}", "\\}").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&").replace("#", "\\#").replace("$", "\\$")
out = ["\\section{Verbatim prompts and tool schema}\n\\label{app:prompts}\n",
       "All prompts are reproduced exactly as sent. The policy sentence is appended to the system prompt; \\texttt{\\{qlang\\}} is the name of the question's language and \\texttt{\\{max\\_searches\\}}=3, \\texttt{\\{k\\}}=5.\n"]
def block(title, text):
    out.append(f"\\paragraph{{{title}}}\n\\begin{{quote}}\\small\\ttfamily\\raggedright\n{esc(text).replace(chr(10), ' \\par ')}\n\\end{{quote}}\n")
block("Agent system prompt", P.SYSTEM_AGENT)
for k, v in P.POLICY.items():
    block(f"Policy sentence: {k}", v.strip() or "(none)")
block("Tool schema (JSON)", json.dumps(P.TOOL_SEARCH, indent=1))
block("Empty-result message", P.NO_RESULTS)
block("Closed-book system prompt", P.SYSTEM_CLOSED)
block("Oracle system prompt", P.SYSTEM_ORACLE)
block("Oracle user message", P.USER_ORACLE)
block("Judge system prompt", P.SYSTEM_JUDGE)
block("Judge user message", P.USER_JUDGE)
(ROOT / "paper" / "iclr" / "appendix_prompts.tex").write_text("\n".join(out))
print("wrote appendix_prompts.tex")
