import requests

latex_code = r"""
\documentclass{article}
\begin{document}
Hello CareerOS! This is compiled via TeXLive.net API.
\end{document}
"""

try:
    print("Compiling LaTeX code via TeXLive.net...")
    resp = requests.post(
        "https://texlive.net/cgi-bin/latexcgi",
        data={
            "filename[]": "document.tex",
            "filecontents[]": latex_code,
            "engine": "pdflatex",
            "return": "pdf"
        }
    )
    if resp.status_code == 200:
        print("Success! PDF received.")
        with open("test_resume.pdf", "wb") as f:
            f.write(resp.content)
        print("Saved to test_resume.pdf")
    else:
        print(f"Failed to compile. Status code: {resp.status_code}, Body: {resp.text[:200]}")
except Exception as e:
    print("Error:", e)
