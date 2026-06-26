import requests

bad_latex = r"""
\documentclass{article}
\begin{document}
Hello & world % This is bad because & and % are unescaped and there is no closing document!
"""

try:
    print("Testing bad compile with files...")
    resp = requests.post(
        "https://texlive.net/cgi-bin/latexcgi",
        files={
            "filename[]": (None, "document.tex"),
            "filecontents[]": (None, bad_latex),
            "engine": (None, "pdflatex"),
            "return": (None, "pdf")
        }
    )
    print(f"Status Code: {resp.status_code}")
    print(f"Content Type: {resp.headers.get('Content-Type')}")
    print(f"Starts with %PDF: {resp.content.startswith(b'%PDF')}")
    print(f"Response Preview (first 1000 chars):\n{resp.text[:1000]}")
except Exception as e:
    print("Error:", e)
