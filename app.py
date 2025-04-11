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

# Admin Model (for storing admin credentials)
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Other Models
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

# Create Database Tables (ensure to run only once)
with app.app_context():
    db.create_all()

# ------------ Routes ------------

# Home Route (Displays Ticket Options)
@app.route("/")
def home():
    return render_template("home.html")

# Get Hotel Room Options
@app.route("/hotel_rooms", methods=["GET"])
def get_hotel_rooms():
    rooms = HotelRoom.query.all()
    return render_template("hotel_rooms.html", rooms=rooms)

# Get Penthouse Options
@app.route("/penthouses", methods=["GET"])
def get_penthouses():
    penthouses = Penthouse.query.all()
    return render_template("penthouses.html", penthouses=penthouses)

# Get Transportation Options
@app.route("/transport_tickets", methods=["GET"])
def get_transport_tickets():
    tickets = TransportationTicket.query.all()
    return render_template("transport_tickets.html", tickets=tickets)

# Get Travel Buddy Options
@app.route("/travel_buddies", methods=["GET"])
def get_travel_buddies():
    buddies = TravelBuddy.query.all()
    return render_template("travel_buddies.html", buddies=buddies)

# ------------ Add New Entries ------------

# Add a Hotel Room
@app.route("/add_hotel_room", methods=["POST"])
def add_hotel_room():
    name = request.form.get("name")
    price = float(request.form.get("price", 0))
    description = request.form.get("description")
    
    new_room = HotelRoom(name=name, price=price, description=description, availability=True)
    db.session.add(new_room)
    db.session.commit()
    
    return redirect("/hotel_rooms")

# Add a Penthouse
@app.route("/add_penthouse", methods=["POST"])
def add_penthouse():
    name = request.form.get("name")
    price = float(request.form.get("price", 0))
    description = request.form.get("description")
    
    new_penthouse = Penthouse(name=name, price=price, description=description, availability=True)
    db.session.add(new_penthouse)
    db.session.commit()
    
    return redirect("/penthouses")

# Add a Transportation Ticket
@app.route("/add_transport_ticket", methods=["POST"])
def add_transport_ticket():
    transport_type = request.form.get("transport_type")
    price = float(request.form.get("price", 0))
    description = request.form.get("description")
    
    new_ticket = TransportationTicket(transport_type=transport_type, price=price, description=description, availability=True)
    db.session.add(new_ticket)
    db.session.commit()
    
    return redirect("/transport_tickets")

# Add a Travel Buddy
@app.route("/add_travel_buddy", methods=["POST"])
def add_travel_buddy():
    name = request.form.get("name")
    destination = request.form.get("destination")
    description = request.form.get("description")
    
    new_buddy = TravelBuddy(name=name, destination=destination, description=description)
    db.session.add(new_buddy)
    db.session.commit()
    
    return redirect("/travel_buddies")

# ------------ Admin Routes ------------

# Admin Signup
@app.route("/admin_signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Create new admin
        new_admin = Admin(username=username)
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()

        flash("Admin account created successfully.", "success")
        return redirect(url_for("admin_login"))
    
    return render_template("admin/signup.html")

# Admin Login
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
            flash("Invalid credentials, please try again.", "danger")
    
    return render_template("admin/login.html")

# Admin Dashboard
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin_id" not in session:
        flash("You need to log in first.", "danger")
        return redirect(url_for("admin_login"))
    
    return render_template("admin/dashboard.html")

# Admin Logout
@app.route("/admin_logout")
def admin_logout():
    session.pop("admin_id", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("admin_login"))

# Run the App
if __name__ == "__main__":
    app.run(debug=True)
