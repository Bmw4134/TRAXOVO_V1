# job_management.py
from flask import Blueprint, render_template, request, redirect, url_for
import json, os

job_bp = Blueprint("job_management", __name__, template_folder="templates/job_management")

JOBS_FILE = "jobs.json"

def register(app):
    app.register_blueprint(job_bp, url_prefix="/job-management")
    app.nav_links.append({
        "label": "Job Zone Config",
        "url": "/job-management",
        "role": "admin"
    })

@job_bp.route("/")
def dashboard():
    jobs = []
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE) as f:
            jobs = json.load(f)
    return render_template("job_management/dashboard.html", jobs=jobs)

@job_bp.route("/edit", methods=["GET", "POST"])
def edit():
    if request.method == "POST":
        new_job = {
            "name": request.form["name"],
            "pm": request.form["pm"],
            "start_time": request.form["start_time"],
            "end_time": request.form["end_time"],
            "night_work": "night_work" in request.form,
            "weekend_allowed": "weekend_allowed" in request.form
        }
        jobs = []
        if os.path.exists(JOBS_FILE):
            with open(JOBS_FILE) as f:
                jobs = json.load(f)
        jobs.append(new_job)
        with open(JOBS_FILE, "w") as f:
            json.dump(jobs, f, indent=2)
        return redirect(url_for("job_management.dashboard"))
    return render_template("job_management/edit.html")