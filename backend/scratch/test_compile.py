import requests

with open("output/TechNovaAI_Computer_Vision___ML_Intern/resume.tex", "r", encoding="utf-8") as f:
    latex_code = f.read()

resp = requests.post(
    "https://texlive.net/cgi-bin/latexcgi",
    files={
        "filename[]": (None, "document.tex"),
        "filecontents[]": (None, latex_code),
        "engine": (None, "pdflatex"),
        "return": (None, "pdf")
    }
)

print("Status Code:", resp.status_code)
if resp.status_code == 200:
    if resp.content.startswith(b"%PDF"):
        print("Successfully generated PDF!")
        with open("output/TechNovaAI_Computer_Vision___ML_Intern/resume_test.pdf", "wb") as f:
            f.write(resp.content)
        print("Saved to output/TechNovaAI_Computer_Vision___ML_Intern/resume_test.pdf")
    else:
        print("API returned 200 but content is not a PDF. Content starts with:")
        print(resp.text[:1000])
else:
    print("Error:", resp.text)
