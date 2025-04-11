from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/ticket_booking"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "ticket_booking_secret"

db = SQLAlchemy(app)

# ------------ Models ------------

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), nullable=True)  
    address = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class HotelRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    availability = db.Column(db.Boolean, default=True)

class TransportationTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transport_type = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    availability = db.Column(db.Boolean, default=True)

class TravelBuddy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)

class Penthouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    availability = db.Column(db.Boolean, default=True)

# Create Database Tables
with app.app_context():
    db.create_all()

# ------------ Public Routes ------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/hotel_rooms")
def get_hotel_rooms():
    rooms = HotelRoom.query.all()
    return render_template("hotel_rooms.html", rooms=rooms)

@app.route("/penthouses")
def get_penthouses():
    penthouses = Penthouse.query.all()
    return render_template("penthouses.html", penthouses=penthouses)

@app.route("/transport_tickets")
def get_transport_tickets():
    tickets = TransportationTicket.query.all()
    return render_template("transport_tickets.html", tickets=tickets)

@app.route("/travel_buddies")
def get_travel_buddies():
    buddies = TravelBuddy.query.all()
    return render_template("travel_buddies.html", buddies=buddies)

# ------------ Add New Entries ------------

@app.route("/add_hotel_room", methods=["POST"])
def add_hotel_room():
    name = request.form.get("name")
    price = float(request.form.get("price", 0))
    description = request.form.get("description")
    new_room = HotelRoom(name=name, price=price, description=description)
    db.session.add(new_room)
    db.session.commit()
    return redirect("/hotel_rooms")

@app.route("/add_penthouse", methods=["POST"])
def add_penthouse():
    name = request.form.get("name")
    price = float(request.form.get("price", 0))
    description = request.form.get("description")
    new_penthouse = Penthouse(name=name, price=price, description=description)
    db.session.add(new_penthouse)
    db.session.commit()
    return redirect("/penthouses")

@app.route("/add_transport_ticket", methods=["POST"])
def add_transport_ticket():
    transport_type = request.form.get("transport_type")
    price = float(request.form.get("price", 0))
    description = request.form.get("description")
    new_ticket = TransportationTicket(transport_type=transport_type, price=price, description=description)
    db.session.add(new_ticket)
    db.session.commit()
    return redirect("/transport_tickets")

@app.route("/add_travel_buddy", methods=["POST"])
def add_travel_buddy():
    name = request.form.get("name")
    destination = request.form.get("destination")
    description = request.form.get("description")
    new_buddy = TravelBuddy(name=name, destination=destination, description=description)
    db.session.add(new_buddy)
    db.session.commit()
    return redirect("/travel_buddies")

# ------------ Admin Auth Routes ------------

@app.route("/admin_signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("admin_signup"))

        if Admin.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return redirect(url_for("admin_signup"))

        new_admin = Admin(username=username)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()

        flash("Admin account created successfully.", "success")
        return redirect(url_for("admin_login"))

    return render_template("admin/signup.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.check_password(password):
            session["admin_id"] = admin.id
            flash("Login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials.", "danger")

    return render_template("admin/login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    return render_template("admin/dashboard.html")

@app.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    if "admin_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("admin_login"))

    admin = Admin.query.get(session["admin_id"])

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        address = request.form.get("address")
        description = request.form.get("description")
        new_password = request.form.get("password")

        if not username or not email:
            flash("Username and email are required.", "danger")
            return redirect(url_for("admin_settings"))

        existing_user = Admin.query.filter(Admin.username == username, Admin.id != admin.id).first()
        existing_email = Admin.query.filter(Admin.email == email, Admin.id != admin.id).first()
        if existing_user:
            flash("Username already taken.", "danger")
            return redirect(url_for("admin_settings"))
        if existing_email:
            flash("Email already used.", "danger")
            return redirect(url_for("admin_settings"))

        admin.username = username
        admin.email = email
        admin.address = address
        admin.description = description

        if new_password:
            admin.set_password(new_password)

        db.session.commit()
        flash("Settings updated successfully.", "success")
        return redirect(url_for("admin_profile"))

    return render_template("admin/settings.html", admin=admin)

@app.route("/admin/profile")
def admin_profile():
    if "admin_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("admin_login"))

    admin = Admin.query.get(session["admin_id"])
    return render_template("admin/profile.html", admin=admin)

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin_id", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("admin_login"))

# Run the App
if __name__ == "__main__":
    app.run(debug=True)
