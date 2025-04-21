from flask import Flask, render_template, request, redirect, flash, session, url_for
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "ticket_booking_secret"

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb+srv://admin:Admin123@all-ticket-booking-syst.2qrnrhs.mongodb.net/ticket_booking?retryWrites=true&w=majority&appName=ALL-Ticket-Booking-System"
mongo = PyMongo(app)

# ------------ Public Routes ------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/hotel_rooms", methods=["GET"])
def get_hotel_rooms():
    rooms = list(mongo.db.hotel_rooms.find())
    return render_template("hotel_rooms.html", rooms=rooms)

@app.route("/penthouses", methods=["GET"])
def get_penthouses():
    penthouses = list(mongo.db.penthouses.find())
    return render_template("penthouses.html", penthouses=penthouses)

@app.route("/transport_tickets")
def get_transport_tickets():
    tickets = list(mongo.db.transportation_tickets.find())
    return render_template("transport_tickets.html", tickets=tickets)

@app.route("/travel_buddies")
def get_travel_buddies():
    buddies = list(mongo.db.travel_buddies.find())
    return render_template("travel_buddies.html", buddies=buddies)

# ------------ Add New Entries ------------

@app.route("/add_hotel_room", methods=["POST"])
def add_hotel_room():
    name = request.form.get("name")
    price = float(request.form.get("price", 0))
    description = request.form.get("description")

    mongo.db.hotel_rooms.insert_one({
        "name": name,
        "price": price,
        "description": description,
        "availability": True
    })
    return redirect("/hotel_rooms")
#st
@app.route('/admin/add_new_hotel_room', methods=['GET', 'POST'])
def add_new_hotel_room():
    if request.method == 'POST':
        room_type = request.form['room_type']
        beds = request.form['beds']
        amenities = request.form['amenities']
        price = request.form['price']
        description = request.form['description']
        image = request.files['image']

        # Save the image to the 'static/uploads' directory
        if image:
            image_path = os.path.join('static/uploads', image.filename)
            image.save(image_path)
        else:
            image_path = None

        # Create a dictionary to store room data
        room_data = {
            'room_type': room_type,
            'beds': beds,
            'amenities': amenities.split(','),
            'price': price,
            'description': description,
            'image': image_path
        }

        # Insert the room data into the MongoDB collection
        mongo.db.hotel_rooms.insert_one(room_data)

        flash("Hotel room added successfully!", "success")
        return redirect(url_for('add_new_hotel_room'))

    return render_template('add_new_hotel_room.html')

#end

@app.route("/add_penthouse", methods=["POST"])
def add_penthouse():
    name = request.form.get("name")
    price = float(request.form.get("price", 0))
    description = request.form.get("description")

    mongo.db.penthouses.insert_one({
        "name": name,
        "price": price,
        "description": description,
        "availability": True
    })
    return redirect("/penthouses")


@app.route('/admin/new-penthouse', methods=['GET', 'POST'])
def add_new_penthouse():
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        location = request.form.get('location')
        price = float(request.form.get('price'))
        features = request.form.get('features')
        image_url = request.form.get('image_url')

        # Data structure to insert
        penthouse_data = {
            "title": title,
            "location": location,
            "price": price,
            "features": features,
            "image_url": image_url
        }

        # Insert into MongoDB
        mongo.db.penthouses.insert_one(penthouse_data)

        flash("Penthouse added and saved to database!", "success")
        return redirect(url_for('add_new_penthouse'))

    return render_template('admin/new_penthouse.html')
#kk
@app.route('/book_penthouse/<penthouse_id>', methods=['POST'])
def book_penthouse(penthouse_id):
    penthouse = mongo.db.penthouses.find_one({'_id': ObjectId(penthouse_id)})
    if penthouse:
        mongo.db.bookings.insert_one({
            'penthouse_id': penthouse['_id'],
            'title': penthouse['title'],
            'price': penthouse['price'],
            'location': penthouse['location'],
            'features': penthouse['features'],
            'image_url': penthouse.get('image_url', ''),
            'status': 'booked'
        })
        flash("Penthouse booked successfully!", "success")
    else:
        flash("Penthouse not found!", "danger")
    return redirect(url_for('view_penthouses'))
#kk

#tt
@app.route('/book-room/<room_id>')
def book_room(room_id):
    room = mongo.db.hotel_rooms.find_one({"_id": room_id})
    if room:
        # Create a booking document in the bookings collection
        booking = {
            "room_id": room["_id"],
            "room_type": room["room_type"],
            "price": room["price"],
            "user_id": "user_123",  # This should be dynamically tied to the logged-in user
            "status": "booked"
        }
        mongo.db.bookings.insert_one(booking)
        flash(f"Room {room['room_type']} has been successfully booked!", "success")
    return redirect(url_for('hotel_rooms'))
#tt

#ss
@app.route('/admin/add_room', methods=['GET', 'POST'])
def add_room():
    if request.method == 'POST':
        room_type = request.form['room_type']
        description = request.form['description']
        price = request.form['price']
        image = request.files['image']

        # Save the image and handle file path here
        if image:
            image_path = 'static/uploads/' + image.filename
            image.save(image_path)

        # Insert the new room into the database
        mongo.db.hotel_rooms.insert_one({
            'room_type': room_type,
            'description': description,
            'price': price,
            'image': image_path
        })

        flash("New room added successfully!", "success")
        return redirect(url_for('hotel_rooms'))

    return render_template('add_room.html')
#ss

#nn
# Route: View + Delete Rooms
@app.route('/admin/manage-rooms')
def manage_hotel_rooms():
    rooms = mongo.db.hotel_rooms.find()
    return render_template('admin/manage_hotel_rooms.html', rooms=rooms)

@app.route('/admin/delete-room/<room_id>', methods=['POST'])
def delete_hotel_room(room_id):
    mongo.db.hotel_rooms.delete_one({'_id': ObjectId(room_id)})
    return redirect(url_for('manage_hotel_rooms'))
#nn

#mm
# Display all penthouses
@app.route('/manage_penthouses')
def manage_penthouses():
    penthouses = list(mongo.db.penthouses.find())
    return render_template('manage_penthouses.html', penthouses=penthouses)

# Delete a specific penthouse
@app.route('/delete_penthouse/<penthouse_id>', methods=['POST'])
def delete_penthouse(penthouse_id):
    mongo.db.penthouses.delete_one({'_id': ObjectId(penthouse_id)})
    flash('Penthouse deleted successfully!', 'success')
    return redirect(url_for('manage_penthouses'))
#mm
@app.route("/add_transport_ticket", methods=["POST"])
def add_transport_ticket():
    transport_type = request.form.get("transport_type")
    price = float(request.form.get("price", 0))
    description = request.form.get("description")

    mongo.db.transportation_tickets.insert_one({
        "transport_type": transport_type,
        "price": price,
        "description": description,
        "availability": True
    })
    return redirect("/transport_tickets")

@app.route("/add_travel_buddy", methods=["POST"])
def add_travel_buddy():
    name = request.form.get("name")
    destination = request.form.get("destination")
    description = request.form.get("description")

    mongo.db.travel_buddies.insert_one({
        "name": name,
        "destination": destination,
        "description": description
    })
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

        if mongo.db.admins.find_one({"username": username}):
            flash("Username already exists.", "danger")
            return redirect(url_for("admin_signup"))

        hashed_password = generate_password_hash(password)
        mongo.db.admins.insert_one({
            "username": username,
            "password_hash": hashed_password
        })
        flash("Admin account created successfully.", "success")
        return redirect(url_for("admin_login"))

    return render_template("admin/signup.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin = mongo.db.admins.find_one({"username": username})

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = str(admin["_id"])
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

    admin = mongo.db.admins.find_one({"_id": ObjectId(session["admin_id"])})

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        address = request.form.get("address")
        description = request.form.get("description")
        new_password = request.form.get("password")

        if not username or not email:
            flash("Username and email are required.", "danger")
            return redirect(url_for("admin_settings"))

        existing_user = mongo.db.admins.find_one({"username": username, "_id": {"$ne": admin["_id"]}})
        existing_email = mongo.db.admins.find_one({"email": email, "_id": {"$ne": admin["_id"]}})

        if existing_user:
            flash("Username already taken.", "danger")
            return redirect(url_for("admin_settings"))
        if existing_email:
            flash("Email already used.", "danger")
            return redirect(url_for("admin_settings"))

        updates = {
            "username": username,
            "email": email,
            "address": address,
            "description": description
        }

        if new_password:
            updates["password_hash"] = generate_password_hash(new_password)

        mongo.db.admins.update_one({"_id": admin["_id"]}, {"$set": updates})
        flash("Settings updated successfully.", "success")
        return redirect(url_for("admin_profile"))

    return render_template("admin/settings.html", admin=admin)


@app.route("/admin/profile")
def admin_profile():
    if "admin_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("admin_login"))

    admin = mongo.db.admins.find_one({"_id": ObjectId(session["admin_id"])})
    return render_template("admin/profile.html", admin=admin)

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin_id", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("admin_login"))

# Run the App
if __name__ == "__main__":
    app.run(debug=True, port=8800)