from flask import Flask, render_template, request, redirect, session, flash ,url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:tiger@localhost/academic_portal'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- FILE UPLOAD ----------------

app.config["UPLOAD_FOLDER"] = "static/reports"
app.config["ZIP_FOLDER"] = "static/zips"

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["ZIP_FOLDER"], exist_ok=True)

# ---------------- DATABASE TABLES ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    Name = db.Column(db.String(100))
    title = db.Column(db.String(200), unique=True)
    Programming_language = db.Column(db.String(50))
    report_file = db.Column(db.String(200))
    zip_file = db.Column(db.String(200))
    status = db.Column(db.String(50), default="Pending")
    suggestion = db.Column(db.Text)

# ---------------- LOGIN PAGE ----------------

@app.route("/")
def login_page():
    return render_template("login.html")

# ---------------- STUDENT LOGIN ----------------

@app.route("/student_login", methods=["POST"])
def student_login():
    username = request.form.get("username")
    password = request.form.get("password")

    pattern = r'^(?=.*[!@#$%^&*(),.?":{}|<>]).{9,}$'

    if not re.match(pattern, password):
        return render_template("login.html", error="Password must be strong")

    user = User.query.filter_by(username=username).first()

    if user and user.password == password:
        session["uid"] = user.id
        return redirect(url_for("dashboard"))

    return render_template("login.html", error="Invalid login")

# ---------------- ADMIN LOGIN ----------------

@app.route("/admin_login", methods=["POST"])
def admin_login():
    username = request.form.get("username")
    password = request.form.get("password")

    if username == "superadmin" and password == "admin@2025":
        session["is_admin"] = True
        return redirect("/admin/dashboard")

    return render_template("login.html", error="Invalid admin login")

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(
            name=request.form.get("name"),
            username=request.form.get("username"),
            password=request.form.get("password")
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/")

    return render_template("register.html")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "uid" not in session:
        return redirect("/")
    return render_template("dashboard.html")

# ---------------- SUBMIT PROJECT ----------------

@app.route("/submit", methods=["GET", "POST"])
def submit_project():

    # Check login
    if "uid" not in session:
        return redirect("/")

    if request.method == "POST":

        # Get form data
        Name = request.form.get("Name")
        title = request.form.get("title")
        Programming_language = request.form.get("Programming_language")

        report = request.files.get("report")
        zipfile = request.files.get("zipfile")

        # Check file upload
        if not report or not zipfile:
            return "⚠️ Please upload both Report and ZIP file"

        # ✅ Duplicate check (case-insensitive)
        existing_project = Project.query.filter(
            db.func.lower(Project.title) == title.strip().lower()
        ).first()

        if existing_project:
            flash("Project title already exists! Try a different title.")
            return render_template("submit_project.html", error="Title already exists")

        # Save files
        report_name = secure_filename(report.filename)
        report_path = os.path.join(app.config["UPLOAD_FOLDER"], report_name)
        report.save(report_path)

        zip_name = secure_filename(zipfile.filename)
        zip_path = os.path.join(app.config["ZIP_FOLDER"], zip_name)
        zipfile.save(zip_path)

        # Save to database
        project = Project(
            Name=Name,
            user_id=session["uid"],
            title=title,
            Programming_language=Programming_language,
            report_file=report_name,
            zip_file=zip_name,
            suggestion="",
            status="Pending"
        )

        db.session.add(project)
        db.session.commit()

        # Redirect to dashboard
        return redirect(url_for("dashboard"))

    return render_template("submit_project.html")
#--------- ------- VIEW ALL PROJECTS (ADMIN) ----------------
@app.route("/all_projects")
def all_projects():

    # Optional: check login
    if "uid" not in session:
        return redirect("/")

    # Get all projects from database
    projects = Project.query.all()

    return render_template("all_projects.html", projects=projects)
# ---------------- VIEW STATUS ----------------

@app.route("/status")
def status():
    if "uid" not in session:
        return redirect("/")

    projects = Project.query.filter_by(user_id=session["uid"]).all()
    return render_template("view_status.html", projects=projects)

# ---------------- ADMIN DASHBOARD ----------------

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("is_admin"):
        return redirect("/")

    projects = Project.query.all()
    return render_template("admin_dashboard.html", projects=projects)

# ---------------- APPROVE ----------------

@app.route("/admin/approve/<int:id>")
def approve(id):
    project = Project.query.get(id)
    project.status = "Approved"
    db.session.commit()
    return redirect("/admin/dashboard")

# ---------------- REJECT ----------------

@app.route("/admin/reject/<int:id>")
def reject(id):
    project = Project.query.get(id)
    project.status = "Rejected"
    db.session.commit()
    return redirect("/admin/dashboard")

# ---------------- ADD SUGGESTION ----------------

@app.route('/add_suggestion/<int:id>', methods=['POST'])
def add_suggestion(id):
    project = Project.query.get(id)
    project.suggestion = request.form.get("suggestion")
    db.session.commit()
    return redirect('/admin/dashboard')

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)