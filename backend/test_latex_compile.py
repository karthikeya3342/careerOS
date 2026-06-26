import requests
import urllib.parse

latex_code = r"""
\documentclass{article}
\begin{document}
Hello CareerOS! This is a compiled LaTeX PDF.
\end{document}
"""

try:
    print("Compiling LaTeX code...")
    encoded = urllib.parse.quote(latex_code)
    resp = requests.get(f"https://latexonline.cc/compile?text={encoded}")
    if resp.status_code == 200:
        print("Success! PDF received.")
        with open("test_resume.pdf", "wb") as f:
            f.write(resp.content)
        print("Saved to test_resume.pdf")
    else:
        print(f"Failed to compile. Status code: {resp.status_code}, Body: {resp.text[:200]}")
except Exception as e:
    print("Error:", e)
