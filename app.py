from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename
from pymongo import MongoClient


app = Flask(__name__)
app.secret_key = "ticket_booking_secret"

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb+srv://admin:Admin123@all-ticket-booking-syst.2qrnrhs.mongodb.net/ticket_booking?retryWrites=true&w=majority&appName=ALL-Ticket-Booking-System"
mongo = PyMongo(app)

# ------------ Public Routes ------------

# ------------ User Auth Routes ------------

@app.route("/")
def home():
    return redirect(url_for("register"))  # 🔁 Redirect to register page if not logged in

# ------------ User Auth Routes ------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not username or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        if mongo.db.users.find_one({"email": email}):
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        mongo.db.users.insert_one({
            "name": name,
            "username": username,
            "email": email,
            "password_hash": hashed_password
        })

        flash("User registered successfully. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("user/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = mongo.db.users.find_one({"email": email})
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = str(user["_id"])
            flash("Login successful!", "success")
            return render_template("home.html") 
        else:
            flash("Invalid credentials.", "danger")

    return render_template("user/login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully.", "success")
    return render_template("user/register.html")


# Settings Page
@app.route("/user/settings", methods=["GET", "POST"])
def user_settings():
    if "user_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("login"))

    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})

    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        description = request.form.get("description")
        profile_pic = request.form.get("profile_pic")
        new_password = request.form.get("password")

        updates = {
            "username": username,
            "email": email,
            "phone": phone,
            "address": address,
            "description": description,
            "profile_pic": profile_pic if profile_pic else user.get("profile_pic")
        }

        if new_password:
            updates["password_hash"] = generate_password_hash(new_password)

        mongo.db.users.update_one({"_id": user["_id"]}, {"$set": updates})
        flash("Profile updated successfully.", "success")
        return redirect(url_for("user_profile"))

    return render_template("user/settings.html", user=user)

@app.route("/user/profile")
def user_profile():
    if "user_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("login"))

    user = mongo.db.users.find_one({"_id": ObjectId(session["user_id"])})
    return render_template("user/profile.html", user=user)


######################################################################################

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
        return redirect(url_for("manage_admins"))

    prefilled_username = request.args.get('username', '')
    return render_template("admin/signup.html", username=prefilled_username)

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

    total_users = mongo.db.users.count_documents({})
    return render_template("admin/dashboard.html", total_users=total_users)

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

# ------------------- View Users -------------------
@app.route('/admin/users')
def view_users():
    users = list(mongo.db.users.find())
    return render_template('admin/view_users.html', users=users)

# ------------------- Delete User -------------------
@app.route('/admin/users/delete/<user_id>', methods=['POST'])
def delete_user(user_id):
    mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    return redirect(url_for('view_users'))

# ------------------- Manage Admins -------------------
@app.route('/admin/manage-admins')
def manage_admins():
    users = list(mongo.db.users.find())
    admin_usernames = set(admin["username"] for admin in mongo.db.admins.find({}, {"username": 1}))
    return render_template('admin/manage_admins.html', users=users, admin_usernames=admin_usernames)

@app.route('/admin/make-admin/<user_id>')
def make_admin(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('manage_admins'))

    # Check if already admin
    if mongo.db.admins.find_one({"username": user["username"]}):
        flash("User is already an admin.", "info")
        return redirect(url_for("manage_admins"))

    # Redirect to signup with prefilled username
    return redirect(url_for('admin_signup', username=user['username']))
##################################################################################################

@app.route("/hotel_rooms", methods=["GET"])
def get_hotel_rooms():
    rooms = list(mongo.db.hotel_rooms.find())
    return render_template("hotel_rooms.html", rooms=rooms)
    


#sttttt
# Route to fetch room details (room numbers + their status)
@app.route('/get-room-details/<room_id>', methods=['GET'])
def get_room_details(room_id):
    # Retrieve the room from the database using the room_id
    room = mongo.db.hotel_rooms.find_one({'_id': ObjectId(room_id)})

    # Check if the room exists
    if room:
        room_numbers = room.get('room_numbers', [])
        
        # Return room numbers and availability status
        available_rooms = [{'number': number, 'status': 'available'} for number in room_numbers]
        return jsonify({'room_numbers': available_rooms})
    return jsonify({'error': 'Room not found'}), 404


@app.route('/book-room', methods=['POST'])
def book_room():
    room_id = request.form.get('room_id')
    room_number = request.form.get('room_number')
    user_name = request.form.get('user_name')

    if not all([room_id, room_number, user_name]):
        flash("All fields are required.", "danger")
        return redirect(url_for('show_rooms'))

    # Mark the selected room number as booked
    mongo.db.rooms.update_one(
        {'_id': ObjectId(room_id), 'room_numbers.number': room_number},
        {'$set': {'room_numbers.$.status': 'booked'}}
    )

    # Log the reservation
    mongo.db.reservations.insert_one({
        'room_id': ObjectId(room_id),
        'room_number': room_number,
        'user_name': user_name,
        'status': 'booked'
    })

    flash('Room booked successfully!', 'success')
    return redirect(url_for('show_rooms'))  # Make sure this route exists


# Admin view to see all reservations
@app.route('/admin/reservations')
def admin_reservations():
    reservations = list(mongo.db.reservations.find())
    return render_template('admin/reservations.html', reservations=reservations)

# Admin cancels a reservation and sets room status back to available
@app.route('/admin/cancel_reservation/<reservation_id>')
def cancel_reservation(reservation_id):
    reservation = mongo.db.reservations.find_one({'_id': ObjectId(reservation_id)})
    if reservation:
        mongo.db.rooms.update_one(
            {'_id': reservation['room_id'], 'room_numbers.number': reservation['room_number']},
            {'$set': {'room_numbers.$.status': 'available'}}
        )
        mongo.db.reservations.delete_one({'_id': ObjectId(reservation_id)})
        flash('Reservation cancelled.', 'warning')
    return redirect(url_for('admin_reservations'))
@app.route('/hotel-rooms')
def show_rooms():
    rooms = list(mongo.db.rooms.find())
    return render_template('hotel_rooms.html', rooms=rooms)

#enddddd

@app.route("/penthouses", methods=["GET"])
def get_penthouses():
    penthouses = list(mongo.db.penthouses.find())
    return render_template("penthouses.html", penthouses=penthouses)

@app.route("/transport_tickets")
def get_transport_tickets():
    tickets = list(mongo.db.transportation_tickets.find())
    return render_template("transport_tickets.html", tickets=tickets)


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


@app.route('/add_new_hotel_room', methods=['GET', 'POST'])
def add_new_hotel_room():
    if request.method == 'POST':
        # Get form data
        room_type = request.form.get('room_type')
        beds = int(request.form.get('beds'))
        amenities = request.form.get('amenities')
        price = float(request.form.get('price'))
        image_url = request.form.get('image_url')
        description = request.form.get('description')
        room_numbers = request.form.getlist('room_numbers[]')  # This will fetch the list of room numbers

        # Data structure to insert
        hotel_room_data = {
            "room_type": room_type,
            "beds": beds,
            "amenities": amenities,
            "price": price,
            "image_url": image_url,
            "description": description,
            "room_numbers": room_numbers  # Adding room numbers to the data structure
        }

        # Insert into MongoDB
        mongo.db.hotel_rooms.insert_one(hotel_room_data)

        flash("Hotel room added successfully!", "success")
        return redirect(url_for('add_new_hotel_room'))

    return render_template('add_new_hotel_room.html')





@app.route('/travel_buddies')
def travel_buddies():
    # Fetch the approved buddies and convert the cursor into a list
    approved_buddies = list(mongo.db.buddies.find({'status': 'approved'}))
    return render_template('travel_buddies.html', buddies=approved_buddies)

    

@app.route('/create_single_buddy', methods=['POST'])
def create_single_buddy():
    name = request.form['name']
    destination = request.form['destination']
    details = request.form['details']
    
    buddy = {
        'type': 'single',
        'name': name,
        'destination': destination,
        'details': details,
        'status': 'pending'
    }
    mongo.db.buddies.insert_one(buddy)
    return redirect(url_for('travel_buddies'))

@app.route('/create_group_buddy', methods=['POST'])
def create_group_buddy():
    group_name = request.form['group_name']
    destination = request.form['destination']
    group_details = request.form['group_details']
    
    buddy = {
        'type': 'group',
        'group_name': group_name,
        'destination': destination,
        'group_details': group_details,
        'status': 'pending'
    }
    mongo.db.buddies.insert_one(buddy)
    return redirect(url_for('travel_buddies'))

# ------------------ Admin Dashboard ------------------

@app.route('/admin/approve_buddy/<buddy_id>')
def approve_buddy(buddy_id):
    mongo.db.buddies.update_one({'_id': ObjectId(buddy_id)}, {'$set': {'status': 'approved'}})
    return redirect(url_for('admin_manage_buddies'))  # Redirect to the manage buddies page, not dashboard




@app.route('/admin/reject_buddy/<buddy_id>')
def reject_buddy(buddy_id):
    mongo.db.buddies.update_one({'_id': ObjectId(buddy_id)}, {'$set': {'status': 'rejected'}})
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/manage_buddies')
def admin_manage_buddies():
    buddies = mongo.db.buddies.find()
    return render_template('admin/manage_buddies.html', buddies=buddies)




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

@app.route('/book-room/<room_id>')
def view_room_booking(room_id):
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

# Route: View + Delete Rooms
@app.route('/admin/manage-rooms')
def manage_hotel_rooms():
    rooms = mongo.db.hotel_rooms.find()
    return render_template('admin/manage_hotel_rooms.html', rooms=rooms)

@app.route('/admin/delete-room/<room_id>', methods=['POST'])
def delete_hotel_room(room_id):
    mongo.db.hotel_rooms.delete_one({'_id': ObjectId(room_id)})
    return redirect(url_for('manage_hotel_rooms'))

# Display all penthouses
@app.route('/manage_penthouses')
def manage_penthouses():
    penthouses = list(mongo.db.penthouses.find())
    return render_template('manage_penthouses.html', penthouses=penthouses)
#rr
@app.route('/edit_hotel_room/<room_id>')
def edit_hotel_room(room_id):
    room = mongo.db.rooms.find_one({'_id': ObjectId(room_id)})
    rooms = list(mongo.db.rooms.find())
    return render_template('admin/manage_hotel_rooms.html', rooms=rooms, room_to_edit=room)

@app.route('/update_hotel_room/<room_id>', methods=['POST'])
def update_hotel_room(room_id):
    updated_data = {
        "room_type": request.form["room_type"],
        "beds": int(request.form["beds"]),
        "amenities": [a.strip() for a in request.form["amenities"].split(',')],
        "price": float(request.form["price"]),
        "description": request.form["description"],
        "image_url": request.form["image_url"]
    }
    mongo.db.rooms.update_one({"_id": ObjectId(room_id)}, {"$set": updated_data})
    return redirect(url_for('admin/manage_hotel_rooms'))
#rr

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

# ------------ Branch Management ------------

@app.route("/admin/branch/add", methods=["GET", "POST"])
def add_branch():
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        address = request.form.get("address")
        details = request.form.get("details")

        if not all([name, email, phone, address]):
            flash("All fields except 'details' are required.", "danger")
            return redirect(url_for("add_branch"))

        # Insert into 'branches' collection in MongoDB
        mongo.db.branches.insert_one({
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "details": details
        })

        flash("Branch added successfully.", "success")
        return redirect(url_for("view_branches"))

    return render_template("admin/branch/add_branch.html")  # Path updated to reflect the correct template location

@app.route("/admin/branch/view")
def view_branches():
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    branches = list(mongo.db.branches.find())
    return render_template("admin/branch/view_branches.html", branches=branches)  # Path updated


# ------------ Transportation System - Bus Routes ------------

@app.route("/admin/transportation/bus/add", methods=["GET", "POST"])
def add_bus_route():
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        date = request.form.get("date")
        fare = request.form.get("fare")
        available_tickets = request.form.get("available_tickets")

        if not all([origin, destination, date, fare, available_tickets]):
            flash("All fields are required.", "danger")
            return redirect(url_for("add_bus_route"))

        origin_branch = mongo.db.branches.find_one({"name": origin})
        destination_branch = mongo.db.branches.find_one({"name": destination})

        if not origin_branch or not destination_branch:
            flash("Origin or destination branch does not exist.", "danger")
            return redirect(url_for("add_bus_route"))

        mongo.db.bus_routes.insert_one({
            "origin": origin,
            "destination": destination,
            "date": datetime.strptime(date, "%Y-%m-%d"),
            "fare": float(fare),
            "available_tickets": int(available_tickets),
            "origin_branch_contact": origin_branch.get("phone"),
            "destination_branch_contact": destination_branch.get("phone")
        })

        flash("Bus route added successfully.", "success")
        return redirect(url_for("view_bus_routes"))

    branches = list(mongo.db.branches.find())
    return render_template("admin/transportation/bus/add_bus_route.html", branches=branches)


@app.route("/admin/transportation/bus/view")
def view_bus_routes():
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    bus_routes = list(mongo.db.bus_routes.find())
    return render_template("admin/transportation/bus/view_bus_routes.html", bus_routes=bus_routes)


# ------------ Transportation System - Train Routes ------------

@app.route("/admin/transportation/train/add", methods=["GET", "POST"])
def add_train_route():
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        date = request.form.get("date")
        fare = request.form.get("fare")
        available_tickets = request.form.get("available_tickets")

        if not all([origin, destination, date, fare, available_tickets]):
            flash("All fields are required.", "danger")
            return redirect(url_for("add_train_route"))

        origin_branch = mongo.db.branches.find_one({"name": origin})
        destination_branch = mongo.db.branches.find_one({"name": destination})

        if not origin_branch or not destination_branch:
            flash("Origin or destination branch does not exist.", "danger")
            return redirect(url_for("add_train_route"))

        mongo.db.train_routes.insert_one({
            "origin": origin,
            "destination": destination,
            "date": datetime.strptime(date, "%Y-%m-%d"),
            "fare": float(fare),
            "available_tickets": int(available_tickets),
            "origin_branch_contact": origin_branch.get("phone"),
            "destination_branch_contact": destination_branch.get("phone")
        })

        flash("Train route added successfully.", "success")
        return redirect(url_for("view_train_routes"))

    branches = list(mongo.db.branches.find())
    return render_template("admin/transportation/train/add_train_route.html", branches=branches)


@app.route("/admin/transportation/train/view")
def view_train_routes():
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    train_routes = list(mongo.db.train_routes.find())
    return render_template("admin/transportation/train/view_train_routes.html", train_routes=train_routes)



# Run the App
if __name__ == "__main__":
    app.run(debug=True, port=8800)