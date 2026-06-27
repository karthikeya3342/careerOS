from flask import Flask, render_template, request, jsonify, send_file, abort
from scrapers import (scrape_linkedin, scrape_glassdoor, scrape_indeed,
                      scrape_hirist, scrape_naukri, scrape_foundit,
                      scrape_apna, scrape_shine)
from scrapers.glassdoor import GLASSDOOR_CITIES
from scrapers.indeed import INDEED_CITIES
from scrapers.hirist import HIRIST_CATEGORIES, HIRIST_CITIES, HIRIST_EXPERIENCE
from scrapers.naukri import NAUKRI_CITIES
from scrapers.foundit import FOUNDIT_CITIES
from scrapers.apna import APNA_CITIES
from scrapers.shine import SHINE_CITIES, SHINE_EXPERIENCE
import pandas as pd
import os

app = Flask(__name__)

# Per-portal cache of the most recent search results
latest = {"linkedin": [], "glassdoor": [], "indeed": [],
          "hirist": [], "naukri": [], "foundit": [],
          "apna": [], "shine": []}


@app.route("/")
def home():
    return render_template("landing.html")


@app.route("/favicon.ico")
def favicon():
    return send_file(
        os.path.join(app.static_folder, "favicon.png"),
        mimetype="image/png",
    )


@app.route("/linkedin")
def linkedin_page():
    return render_template("linkedin.html")


@app.route("/glassdoor")
def glassdoor_page():
    return render_template("glassdoor.html", cities=list(GLASSDOOR_CITIES.keys()))


@app.route("/indeed")
def indeed_page():
    return render_template("indeed.html", cities=list(INDEED_CITIES.keys()))


@app.route("/hirist")
def hirist_page():
    return render_template(
        "hirist.html",
        categories=HIRIST_CATEGORIES,
        cities=list(HIRIST_CITIES.keys()),
        experiences=list(HIRIST_EXPERIENCE.keys()),
    )


@app.route("/naukri")
def naukri_page():
    return render_template("naukri.html", cities=list(NAUKRI_CITIES.keys()))


@app.route("/foundit")
def foundit_page():
    return render_template("foundit.html", cities=list(FOUNDIT_CITIES.keys()))


@app.route("/apna")
def apna_page():
    return render_template("apna.html", cities=list(APNA_CITIES.keys()))


@app.route("/shine")
def shine_page():
    return render_template(
        "shine.html",
        cities=list(SHINE_CITIES.keys()),
        experiences=SHINE_EXPERIENCE,
    )


@app.route("/search/linkedin", methods=["POST"])
def search_linkedin():
    try:
        role        = request.form.get("role", "").strip()
        time_filter = int(request.form.get("time_filter", 86400))
        limit       = int(request.form.get("limit", 10))
        apply_mode  = request.form.get("apply_mode", "include_easy").strip().lower()
        locations   = request.form.getlist("locations")

        if not role:
            return jsonify({"error": "Please enter a job role"}), 400
        if not locations:
            return jsonify({"error": "Select at least one location"}), 400
        if apply_mode not in {"include_easy", "only_easy", "only_external"}:
            return jsonify({"error": "Invalid apply filter selected"}), 400

        jobs = scrape_linkedin(
            role=role,
            time_filter=time_filter,
            limit=limit,
            locations=locations,
            apply_mode=apply_mode,
        )
        latest["linkedin"] = jobs
        return jsonify({"jobs": jobs, "count": len(jobs), "requested": limit})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/glassdoor", methods=["POST"])
def search_glassdoor():
    try:
        role        = request.form.get("role", "").strip()
        from_age    = int(request.form.get("from_age", 1))
        limit       = int(request.form.get("limit", 10))
        apply_mode  = request.form.get("apply_mode", "include_easy").strip().lower()
        locations   = request.form.getlist("locations")

        if not role:
            return jsonify({"error": "Please enter a job role"}), 400
        if not locations:
            return jsonify({"error": "Select at least one location"}), 400
        if apply_mode not in {"include_easy", "only_easy", "only_external"}:
            return jsonify({"error": "Invalid apply filter selected"}), 400

        jobs = scrape_glassdoor(
            role=role,
            from_age_days=from_age,
            limit=limit,
            locations=locations,
            apply_mode=apply_mode,
        )
        latest["glassdoor"] = jobs
        return jsonify({"jobs": jobs, "count": len(jobs), "requested": limit})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/indeed", methods=["POST"])
def search_indeed():
    try:
        role        = request.form.get("role", "").strip()
        fromage     = int(request.form.get("fromage", 1))
        limit       = int(request.form.get("limit", 10))
        apply_mode  = request.form.get("apply_mode", "include_easy").strip().lower()
        locations   = request.form.getlist("locations")

        if not role:
            return jsonify({"error": "Please enter a job role"}), 400
        if not locations:
            return jsonify({"error": "Select at least one location"}), 400
        if apply_mode not in {"include_easy", "only_easy", "only_external"}:
            return jsonify({"error": "Invalid apply filter selected"}), 400

        jobs = scrape_indeed(
            role=role,
            fromage_days=fromage,
            limit=limit,
            locations=locations,
            apply_mode=apply_mode,
        )
        latest["indeed"] = jobs
        return jsonify({"jobs": jobs, "count": len(jobs), "requested": limit})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/hirist", methods=["POST"])
def search_hirist():
    try:
        role        = request.form.get("role", "").strip()  # role here = category slug
        city        = request.form.get("city", "").strip()
        exp_key     = request.form.get("experience", "any").strip()
        posting     = int(request.form.get("posting", 3))
        limit       = int(request.form.get("limit", 10))

        if not role:
            return jsonify({"error": "Please select a job category"}), 400
        if not city:
            return jsonify({"error": "Please select a location"}), 400
        if role not in HIRIST_CATEGORIES:
            return jsonify({"error": "Unknown category"}), 400
        if city not in HIRIST_CITIES:
            return jsonify({"error": "Unknown city"}), 400
        if exp_key not in HIRIST_EXPERIENCE:
            return jsonify({"error": "Unknown experience range"}), 400

        jobs = scrape_hirist(
            category=role,
            city=city,
            exp_key=exp_key,
            posting_days=posting,
            limit=limit,
        )
        latest["hirist"] = jobs
        return jsonify({"jobs": jobs, "count": len(jobs), "requested": limit})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/naukri", methods=["POST"])
def search_naukri():
    try:
        role        = request.form.get("role", "").strip()
        city        = request.form.get("city", "").strip()
        job_age     = int(request.form.get("job_age", 7))
        limit       = int(request.form.get("limit", 10))
        exp_raw     = (request.form.get("experience") or "").strip()
        experience  = int(exp_raw) if exp_raw else None

        if not role:
            return jsonify({"error": "Please enter a job role"}), 400
        if not city:
            return jsonify({"error": "Please select a location"}), 400
        if city not in NAUKRI_CITIES:
            return jsonify({"error": "Unknown city"}), 400

        jobs = scrape_naukri(
            role=role, city=city, job_age_days=job_age,
            limit=limit, experience=experience,
        )
        latest["naukri"] = jobs
        return jsonify({"jobs": jobs, "count": len(jobs), "requested": limit})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/foundit", methods=["POST"])
def search_foundit():
    try:
        role        = request.form.get("role", "").strip()
        city        = request.form.get("city", "").strip()
        freshness   = int(request.form.get("freshness", 7))
        limit       = int(request.form.get("limit", 10))
        exp_raw     = (request.form.get("experience") or "").strip()
        experience  = int(exp_raw) if exp_raw else None

        if not role:
            return jsonify({"error": "Please enter a job role"}), 400
        if not city:
            return jsonify({"error": "Please select a location"}), 400
        if city not in FOUNDIT_CITIES:
            return jsonify({"error": "Unknown city"}), 400

        jobs = scrape_foundit(
            role=role, city=city, job_freshness_days=freshness,
            limit=limit, experience=experience,
        )
        latest["foundit"] = jobs
        return jsonify({"jobs": jobs, "count": len(jobs), "requested": limit})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/apna", methods=["POST"])
def search_apna():
    try:
        role        = request.form.get("role", "").strip()
        city        = request.form.get("city", "").strip()
        posted_in   = int(request.form.get("posted_in", 0))
        limit       = int(request.form.get("limit", 10))
        min_raw     = (request.form.get("min_experience") or "").strip()
        max_raw     = (request.form.get("max_experience") or "").strip()
        min_exp     = int(min_raw) if min_raw else None
        max_exp     = int(max_raw) if max_raw else None

        if not role:
            return jsonify({"error": "Please enter a job role"}), 400
        if not city:
            return jsonify({"error": "Please select a location"}), 400
        if city not in APNA_CITIES:
            return jsonify({"error": "Unknown city"}), 400

        jobs = scrape_apna(
            role=role, city=city, posted_in_days=posted_in,
            limit=limit, min_experience=min_exp, max_experience=max_exp,
        )
        latest["apna"] = jobs
        return jsonify({"jobs": jobs, "count": len(jobs), "requested": limit})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search/shine", methods=["POST"])
def search_shine():
    try:
        role         = request.form.get("role", "").strip()
        city         = request.form.get("city", "").strip()
        posting_days = int(request.form.get("posting_days", 0))
        limit        = int(request.form.get("limit", 10))
        fexp         = request.form.getlist("fexp")

        if not role:
            return jsonify({"error": "Please enter a job role"}), 400
        if not city:
            return jsonify({"error": "Please select a location"}), 400
        if city not in SHINE_CITIES:
            return jsonify({"error": "Unknown city"}), 400
        for v in fexp:
            if v not in SHINE_EXPERIENCE:
                return jsonify({"error": f"Unknown experience band: {v}"}), 400

        jobs = scrape_shine(
            role=role, city=city, fexp=fexp,
            posting_days=posting_days, limit=limit,
        )
        latest["shine"] = jobs
        return jsonify({"jobs": jobs, "count": len(jobs), "requested": limit})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/<source>")
def download(source):
    source = source.lower()
    if source not in latest:
        abort(404)
    data = latest[source]
    if not data:
        return "No data. Run a search first.", 400

    df = pd.DataFrame(data)
    df["Source"] = {"linkedin": "LinkedIn", "glassdoor": "Glassdoor",
                    "indeed": "Indeed", "hirist": "Hirist",
                    "naukri": "Naukri", "foundit": "Foundit",
                    "apna": "Apna", "shine": "Shine"}.get(source, source.capitalize())

    df.rename(columns={"Company": "Company Name"}, inplace=True)
    # Columns vary by portal; include any that exist.
    column_order = ["Link", "Company Name", "Job Title", "Location", "Source",
                    "Posted", "Experience", "Workplace", "Seniority", "Rating",
                    "Salary", "Skills", "Industry", "Description", "Source ATS",
                    "Easy Apply", "Apply Type"]
    df = df[[c for c in column_order if c in df.columns]]

    path = os.path.join(os.path.dirname(__file__), f"jobs_{source}.xlsx")
    df.to_excel(path, index=False)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
