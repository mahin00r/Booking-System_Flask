from flask import Flask, render_template, request, redirect, flash, session, url_for, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import os,sys
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from pymongo import ReturnDocument
from datetime import datetime
from bson.errors import InvalidId




app = Flask(__name__)
app.secret_key = "ticket_booking_secret"

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb+srv://admin:Admin123@all-ticket-booking-syst.2qrnrhs.mongodb.net/ticket_booking?retryWrites=true&w=majority&appName=ALL-Ticket-Booking-System"
mongo = PyMongo(app)
bus_routes_collection = mongo.db.bus_routes

# ------------ Public Routes ------------

# ------------ User Auth Routes ------------

# ------------ Prevent Back Navigation to Login/Register After Login ------------

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store"
    return response

# ------------ Routes ------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("home"))
    return redirect(url_for("register"))

@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("home.html")

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
            return redirect(url_for("home"))  # ✅ Use redirect instead of render
        else:
            flash("Invalid credentials.", "danger")

    return render_template("user/login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("register"))

# ------------ User Settings and Profile ------------

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
        profile_pic = request.form.get("profile_pic")  # ✅ NEW FIELD
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
            "description": description,
            "profile_pic": profile_pic if profile_pic else admin.get("profile_pic")  # ✅ Conditional Update
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
    room = mongo.db.hotel_rooms.find_one({'_id': ObjectId(room_id)})

    if room:
        room_numbers = room.get('room_numbers', [])
        available_rooms = []

        for room_entry in room_numbers:
            if isinstance(room_entry, dict):
                number = room_entry.get('number')
                status = room_entry.get('status', 'available')
            else:
                number = room_entry
                status = 'available'
            available_rooms.append({'number': number, 'status': status})

        return jsonify({'room_numbers': available_rooms})
    
    return jsonify({'error': 'Room not found'}), 404


@app.route('/book-room', methods=['POST'])
def book_room():
    form = request.form
    room_id = form.get('room_id')
    room_number = form.get('room_number')
    user_name = form.get('user_name')
    email = form.get('email')
    phone = form.get('phone')
    checkin_date = form.get('checkin_date')
    checkout_date = form.get('checkout_date')
    guests = form.get('guests')
    bed_type = form.get('bed_type')
    smoking = form.get('smoking')
    view_preference = form.get('view_preference')
    floor_preference = form.get('floor_preference')
    
    # Handle optional Add-on Services
    breakfast = form.get('breakfast', 'No')
    airport_pickup = form.get('airport_pickup', 'No')
    late_checkout = form.get('late_checkout', 'No')
    early_checkin = form.get('early_checkin', 'No')
    extra_bed = form.get('extra_bed', 'No')
    wifi_upgrade = form.get('wifi_upgrade', 'No')
    mini_bar = form.get('mini_bar', 'No')
    laundry = form.get('laundry', 'No')
    parking = form.get('parking', 'No')
    pet_friendly = form.get('pet_friendly', 'No')
    room_decor = form.get('room_decor', 'No')
    spa_gym_pool = form.get('spa_gym_pool', 'No')

    # Collect all selected add-ons into a dictionary
    # Assuming this block captures the add-ons and stores them as an object
    add_ons = {
    "high_speed_wifi": form.get('wifi_upgrade', 'No'),
    "mini_bar": form.get('mini_bar', 'No'),
    "laundry_service": form.get('laundry', 'No'),
    "parking_spot": form.get('parking', 'No'),
    "pet_friendly": form.get('pet_friendly', 'No'),
    "room_decoration": form.get('room_decor', 'No'),
    "breakfast_included": form.get('breakfast', 'No'),
    "airport_pickup": form.get('airport_pickup', 'No'),
    "late_checkout": form.get('late_checkout', 'No'),
    "early_checkin": form.get('early_checkin', 'No'),
    "extra_bed": form.get('extra_bed', 'No'),
    "spa_access": form.get('facilities', 'No')
}


    # Validate required fields
    if not all([room_id, room_number, user_name, email, phone, checkin_date, checkout_date]):
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for('get_hotel_rooms'))

    # Check if the selected room number is already booked
    room = mongo.db.hotel_rooms.find_one({
        '_id': ObjectId(room_id),
        'room_numbers': {
            '$elemMatch': {
                'number': room_number,
                'status': 'booked'
            }
        }
    })

    if room:
        flash(f"Room {room_number} is already booked.", "danger")
        return redirect(url_for('get_hotel_rooms'))

    # Mark room number as booked in the hotel_rooms collection
    mongo.db.hotel_rooms.update_one(
        {'_id': ObjectId(room_id), 'room_numbers.number': room_number},
        {'$set': {'room_numbers.$.status': 'booked'}}
    )

    # Save the booking into the reservations collection
    reservation = {
        'room_id': ObjectId(room_id),
        'room_number': room_number,
        'user_name': user_name,
        'email': email,
        'phone': phone,
        'checkin_date': checkin_date,
        'checkout_date': checkout_date,
        'guests': guests,
        'bed_type': bed_type,
        'smoking': smoking,
        'view_preference': view_preference,
        'floor_preference': floor_preference,
        'add_ons': add_ons,  # Store the add-ons as a dictionary
        'special_requests': form.get('special_requests', ''),
        'status': 'booked',
        'created_at': datetime.utcnow()
    }

    # Insert the reservation into the MongoDB reservations collection
    mongo.db.reservations.insert_one(reservation)

    flash(f"Room {room_number} booked successfully!", "success")
    return redirect(url_for('get_hotel_rooms'))

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
        room_numbers_input = request.form.getlist('room_numbers[]')

        # Convert amenities to a list
        amenities_list = [amenity.strip() for amenity in amenities.split(',') if amenity.strip()]

        # Create room_numbers as a list of dictionaries
        room_numbers = [{'number': rn.strip(), 'status': 'available'} for rn in room_numbers_input if rn.strip()]

        # Data structure to insert
        hotel_room_data = {
            "room_type": room_type,
            "beds": beds,
            "amenities": amenities_list,
            "price": price,
            "image_url": image_url,
            "description": description,
            "room_numbers": room_numbers
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
    trip_title = request.form['trip_title']
    destination = request.form['destination']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    trip_type = request.form['trip_type']
    gender_preference = request.form['gender_preference']
    age_preference = request.form.get('age_preference')
    budget = request.form.get('budget')
    mode_of_travel = request.form['mode_of_travel']
    accommodation_preference = request.form['accommodation_preference']
    short_bio = request.form['short_bio']
    contact_option = request.form['contact_option']

    buddy = {
        'type': 'single',
        'trip_title': trip_title,
        'destination': destination,
        'start_date': start_date,
        'end_date': end_date,
        'trip_type': trip_type,
        'gender_preference': gender_preference,
        'age_preference': age_preference if age_preference else None,
        'budget': budget if budget else None,
        'mode_of_travel': mode_of_travel,
        'accommodation_preference': accommodation_preference,
        'short_bio': short_bio,
        'contact_option': contact_option,
        'status': 'pending'
    }

    mongo.db.buddies.insert_one(buddy)
    return redirect(url_for('travel_buddies'))


@app.route('/create_group_buddy', methods=['POST'])
def create_group_buddy():
    trip_title = request.form['trip_title']
    destination = request.form['destination']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    group_size = request.form['group_size']
    looking_for_more = request.form['looking_for_more']
    group_type = request.form['group_type']
    age_range = request.form['age_range']
    gender_composition = request.form['gender_composition']
    trip_type = request.form['trip_type']
    budget_range = request.form['budget_range']
    accommodation_plan = request.form['accommodation_plan']
    group_bio = request.form['group_bio']
    contact_option = request.form['contact_option']

    buddy = {
        'type': 'group',
        'trip_title': trip_title,
        'destination': destination,
        'start_date': start_date,
        'end_date': end_date,
        'group_size': group_size,
        'looking_for_more': looking_for_more,
        'group_type': group_type,
        'age_range': age_range,
        'gender_composition': gender_composition,
        'trip_type': trip_type,
        'budget_range': budget_range,
        'accommodation_plan': accommodation_plan,
        'group_bio': group_bio,
        'contact_option': contact_option,
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


@app.route("/book_penthouse/<penthouse_id>", methods=["GET", "POST"])
def book_penthouse(penthouse_id):
    penthouse = mongo.db.penthouses.find_one({"_id": ObjectId(penthouse_id)})
    
    if not penthouse:
        return "Penthouse not found", 404
    
    if request.method == "POST":
        # Get form data, with a default value of 0 if empty
        adults = request.form.get("adults")
        children = request.form.get("children")
        
        # Convert to int, defaulting to 0 if the value is empty
        try:
            adults = int(adults) if adults else 0
            children = int(children) if children else 0
        except ValueError:
            # Handle case where the value can't be converted
            flash("Please enter valid numbers for adults and children.", "danger")
            return redirect(request.url)
        
        booking = {
            "penthouse_id": penthouse_id,
            "penthouse_name": penthouse.get("title"),
            "location": penthouse.get("location"),
            "check_in": request.form.get("check_in"),
            "check_out": request.form.get("check_out"),
            "adults": adults,
            "children": children,
            "room_type": request.form.get("room_type"),
            "services": request.form.getlist("services"),
            "user_name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "payment_method": request.form.get("payment_method"),
            "promo_code": request.form.get("promo_code"),
            "status": "Pending Confirmation",
            "timestamp": datetime.now()
        }
        
        # Insert booking data into the database
        mongo.db.bookings.insert_one(booking)

        # Flash success message and redirect to the booking confirmation page
        flash("Penthouse booked successfully!", "success")
        return redirect(url_for("booking_success"))  # Redirect to the success page
    
    return render_template("book_penthouse.html", penthouse=penthouse)



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
    rooms_cursor = mongo.db.hotel_rooms.find()
    rooms = []
    for room in rooms_cursor:
        room['_id'] = str(room['_id'])
        rooms.append(room)

    reservations_cursor = mongo.db.bookings.find()
    reservations = []
    for res in reservations_cursor:
        res['_id'] = str(res['_id'])
        reservations.append(res)

    room_to_edit = None
    return render_template('admin/manage_hotel_rooms.html', rooms=rooms, reservations=reservations, room_to_edit=room_to_edit)



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
    room_to_edit = mongo.db.rooms.find_one({"_id": ObjectId(room_id)})
    rooms = list(mongo.db.rooms.find())  # Fetch all rooms again

    return render_template(
        '/admin/manage_hotel_rooms.html',
        room_to_edit=room_to_edit,
        rooms=rooms
    )


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
    return redirect(url_for('/admin/manage_hotel_rooms'))
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

##pent

@app.route("/book_penthouse/<penthouse_id>", methods=["GET", "POST"])
def book_penthouse_view(penthouse_id):
    penthouse = mongo.db.penthouses.find_one({"_id": ObjectId(penthouse_id)})
    if not penthouse:
        return "Penthouse not found", 404

    if request.method == "POST":
        booking = {
            "penthouse_id": penthouse_id,
            "penthouse_name": penthouse.get("title"),
            "location": penthouse.get("location"),
            "check_in": request.form.get("check_in"),
            "check_out": request.form.get("check_out"),
            "adults": int(request.form.get("adults")),
            "children": int(request.form.get("children")),
            "room_type": request.form.get("room_type"),
            "services": request.form.getlist("services"),
            "user_name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "payment_method": request.form.get("payment_method"),
            "promo_code": request.form.get("promo_code"),
            "status": "Pending Confirmation",
            "timestamp": datetime.now()
        }
        mongo.db.bookings.insert_one(booking)
        return redirect(url_for("booking_success")) 
    return render_template("book_penthouse.html", penthouse=penthouse)

@app.route("/booking-success")
def booking_success():
    return "<h2>✅ Your booking has been submitted!</h2><a href='/'>Return to Home</a>"
@app.route("/manage_reservations", methods=["GET"])
def manage_reservations():
    # Fetch all bookings related to penthouses
    reservations = list(mongo.db.bookings.find({"penthouse_id": {"$exists": True}}))  # Ensure the reservation is for a penthouse
    
    # Pass the reservations to the template
    return render_template("manage_reservations.html", reservations=reservations)

@app.route("/cancel_reservations/<reservation_id>/<penthouse_id>", methods=["GET"])
def cancel_reservations(reservation_id, penthouse_id):
    try:
        # Update reservation status to 'Cancelled'
        result = mongo.db.bookings.update_one(
            {"_id": ObjectId(reservation_id)},
            {"$set": {"status": "Cancelled"}}
        )

        if result.matched_count > 0:
            flash("Reservation has been cancelled.", "success")
        else:
            flash("Reservation not found or already cancelled.", "warning")

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "danger")

    # After cancellation, redirect to the manage reservations page
    return redirect(url_for("manage_reservations"))

##pent

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
        time = request.form.get("time")
        seat_class = request.form.get("seat_type")  # 🔄 corrected field name
        fare = request.form.get("fare")
        available_tickets = request.form.get("available_tickets")

        if not all([origin, destination, date, time, seat_class, available_tickets]):
            flash("All fields except fare are required.", "danger")
            return redirect(url_for("add_bus_route"))

        # Auto-fare based on seat class if empty
        if not fare:
            if seat_class == "Economy":
                fare = 400
            elif seat_class == "Business":
                fare = 800
            elif seat_class == "Regular":
                fare = 600
            else:
                flash("Invalid seat class.", "danger")
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
            "time": time,
            "seat_class": seat_class,
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

@app.route("/admin/transportation/bus/edit/<route_id>", methods=["GET", "POST"])
def edit_bus_route(route_id):
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    route = mongo.db.bus_routes.find_one({"_id": ObjectId(route_id)})
    if not route:
        flash("Bus route not found.", "danger")
        return redirect(url_for("view_bus_routes"))

    branches = list(mongo.db.branches.find())

    if request.method == "POST":
        updated_data = {
            "origin": request.form.get("origin"),
            "destination": request.form.get("destination"),
            "date": datetime.strptime(request.form.get("date"), "%Y-%m-%d"),
            "time": request.form.get("time"),
            "seat_class": request.form.get("seat_class"),
            "fare": float(request.form.get("fare")),
            "available_tickets": int(request.form.get("available_tickets")),
        }

        origin_branch = mongo.db.branches.find_one({"name": updated_data["origin"]})
        destination_branch = mongo.db.branches.find_one({"name": updated_data["destination"]})

        updated_data["origin_branch_contact"] = origin_branch.get("phone") if origin_branch else ""
        updated_data["destination_branch_contact"] = destination_branch.get("phone") if destination_branch else ""

        mongo.db.bus_routes.update_one({"_id": ObjectId(route_id)}, {"$set": updated_data})
        flash("Bus route updated successfully.", "success")
        return redirect(url_for("view_bus_routes"))

    return render_template("admin/transportation/bus/edit_bus_route.html", route=route, branches=branches)

@app.route("/admin/transportation/bus/delete/<route_id>")
def delete_bus_route(route_id):
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    result = mongo.db.bus_routes.delete_one({"_id": ObjectId(route_id)})
    if result.deleted_count:
        flash("Bus route deleted successfully.", "success")
    else:
        flash("Bus route not found.", "danger")
    return redirect(url_for("view_bus_routes"))

# ------------ Transportation System - Car Routes ------------

# Add Car Route
@app.route("/admin/transportation/car/add", methods=["GET", "POST"])
def add_car_route():
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        date = request.form.get("date")
        car_type = request.form.get("car_type")
        fare = request.form.get("fare")
        available_cars = request.form.get("available_cars")

        # Check if required fields are filled
        if not all([origin, destination, date, car_type, available_cars]):
            flash("All fields except fare are required.", "danger")
            return redirect(url_for("add_car_route"))

        # Auto-fare based on car type if fare is empty
        if not fare:
            if car_type == "Small":
                fare = 2000
            elif car_type == "Large":
                fare = 3000
            elif car_type == "Extra Large":
                fare = 4000
            else:
                flash("Invalid car type.", "danger")
                return redirect(url_for("add_car_route"))

        # Check if origin and destination branches exist
        origin_branch = mongo.db.branches.find_one({"name": origin})
        destination_branch = mongo.db.branches.find_one({"name": destination})

        if not origin_branch or not destination_branch:
            flash("Origin or destination branch does not exist.", "danger")
            return redirect(url_for("add_car_route"))

        # Insert new car route into MongoDB
        mongo.db.car_routes.insert_one({
            "origin": origin,
            "destination": destination,
            "date": datetime.strptime(date, "%Y-%m-%d"),
            "car_type": car_type,
            "fare": float(fare),
            "available_cars": int(available_cars),
            "origin_branch_contact": origin_branch.get("phone"),
            "destination_branch_contact": destination_branch.get("phone")
        })

        flash("Car route added successfully.", "success")
        return redirect(url_for("view_car_routes"))

    branches = list(mongo.db.branches.find())
    return render_template("admin/transportation/car/add_car_route.html", branches=branches)

# View Car Routes
@app.route("/admin/transportation/car/view", methods=["GET"])
def view_car_routes():
    if "admin_id" not in session:
        flash("Login required.", "danger")
        return redirect(url_for("admin_login"))

    car_routes = mongo.db.car_routes.find()
    return render_template("admin/transportation/car/view_car_routes.html", car_routes=car_routes)

# Edit Car Route
@app.route('/edit_car_route/<route_id>', methods=['GET', 'POST'])
def edit_car_route(route_id):
    # Find the car route to edit
    route = mongo.db.car_routes.find_one({'_id': ObjectId(route_id)})

    if request.method == 'POST':
        origin = request.form['origin']
        destination = request.form['destination']
        date = request.form['date']
        car_type = request.form['car_type']
        fare = request.form['fare']
        available_cars = request.form['available_cars']

        # Update the route data in MongoDB
        mongo.db.car_routes.update_one(
            {'_id': ObjectId(route_id)},
            {'$set': {
                'origin': origin,
                'destination': destination,
                'date': datetime.strptime(date, '%Y-%m-%d'),
                'car_type': car_type,
                'fare': float(fare),
                'available_cars': int(available_cars)
            }}
        )
        flash("Car route updated successfully.", "success")
        return redirect(url_for('view_car_routes'))

    # Fetch branches for dropdown in the form
    branches = mongo.db.branches.find()
    return render_template('admin/transportation/car/edit_car_route.html', route=route, branches=branches)

# Delete Car Route
@app.route('/delete_car_route/<route_id>', methods=['GET'])
def delete_car_route(route_id):
    mongo.db.car_routes.delete_one({'_id': ObjectId(route_id)})
    flash("Car route deleted successfully.", "success")
    return redirect(url_for('view_car_routes'))

############### USER PART BOOKING (BUS) ###############################

@app.route('/show-bus-tickets')
def show_bus_tickets():
    routes_cursor = bus_routes_collection.find()
    
    routes = []
    for route in routes_cursor:
        route['_id'] = str(route['_id'])  # Convert ObjectId for URL

        # Format date and time safely
        if isinstance(route.get('date'), datetime):
            route['formatted_date'] = route['date'].strftime('%B %d, %Y')
        else:
            route['formatted_date'] = route.get('date', 'N/A')

        if isinstance(route.get('time'), str):
            try:
                parsed_time = datetime.strptime(route['time'], '%H:%M')
                route['formatted_time'] = parsed_time.strftime('%I:%M %p')
            except:
                route['formatted_time'] = route['time']
        else:
            route['formatted_time'] = 'N/A'

        route['available_tickets'] = int(route.get('available_tickets', 0))
        routes.append(route)

    return render_template('user/show_bus_tickets.html', routes=routes)

@app.route("/book-ticket/<route_id>", methods=["GET", "POST"])
def book_bus_ticket(route_id):
    route = mongo.db.bus_routes.find_one({"_id": ObjectId(route_id)})

    if not route:
        flash("Route not found.", "danger")
        return redirect(url_for("show_bus_tickets"))

    if request.method == "POST":
        try:
            seats = int(request.form.get("seats"))
            name = request.form.get("name")
            phone = request.form.get("phone")
            email = request.form.get("email")
            address = request.form.get("address")

            if seats <= 0 or seats > route.get("available_tickets", 0):
                flash("Invalid number of seats selected.", "danger")
                return redirect(request.url)

            # Format date and time
            booking_date = route.get("date")
            booking_time = route.get("time", "00:00")
            if isinstance(booking_date, datetime):
                formatted_date = booking_date.strftime("%B %d, %Y")
            else:
                formatted_date = booking_date or "N/A"

            try:
                formatted_time = datetime.strptime(booking_time, "%H:%M").strftime("%I:%M %p")
            except:
                formatted_time = booking_time or "N/A"

            # Insert booking into `bus_bookings` collection
            booking = {
                "route_id": str(route["_id"]),
                "origin": route.get("origin", "Unknown"),
                "destination": route.get("destination", "Unknown"),
                "date": formatted_date,
                "time": formatted_time,
                "name": name,
                "phone": phone,
                "email": email,
                "address": address,
                "seats": seats,
                "fare_per_seat": route["fare"],
                "total_fare": float(route["fare"]) * seats,
                "booking_time": datetime.now(),
                "status": "Booked"  # ✅ Set status to avoid 'status' error
            }

            mongo.db.bus_bookings.insert_one(booking)

            # Update available tickets
            mongo.db.bus_routes.update_one(
                {"_id": ObjectId(route_id)},
                {"$inc": {"available_tickets": -seats}}
            )

            flash("Ticket booked successfully!", "success")
            return redirect(url_for("show_bus_tickets"))

        except Exception as e:
            flash(f"An error occurred while booking: {str(e)}", "danger")
            return redirect(request.url)

    # Prepare data for GET request rendering
    route['_id'] = str(route['_id'])
    route['available_tickets'] = int(route.get('available_tickets', 0))

    if isinstance(route.get("date"), datetime):
        route["formatted_date"] = route["date"].strftime("%B %d, %Y")
    else:
        route["formatted_date"] = route.get("date", "N/A")

    try:
        route["formatted_time"] = datetime.strptime(route.get("time", "00:00"), "%H:%M").strftime("%I:%M %p")
    except:
        route["formatted_time"] = route.get("time", "N/A")

    return render_template("user/book_bus_ticket.html", route=route)


@app.route("/admin/manage_bus_reservations")
def manage_bus_reservations():
    # Fetch only active (not cancelled) reservations
    reservations = mongo.db.bus_bookings.find({"status": {"$ne": "Cancelled"}})
    return render_template("admin/manage_bus_reservations.html", reservations=reservations)

@app.route("/admin/cancel_bus_reservation/<reservation_id>", methods=["GET"])
def cancel_bus_reservation(reservation_id):
    try:
        # Ensure reservation_id is an ObjectId
        reservation_id = ObjectId(reservation_id)
        print(f"Attempting to cancel reservation with ID: {reservation_id}", file=sys.stderr)

        # Fetch the reservation document from MongoDB
        reservation = mongo.db.bus_bookings.find_one({"_id": reservation_id})
        print("Fetched reservation:", reservation, file=sys.stderr)

        if reservation:
            # Ensure status is not already "Cancelled"
            if reservation.get("status") != "Cancelled":
                # Attempt to update the reservation's status to "Cancelled"
                result = mongo.db.bus_bookings.update_one(
                    {"_id": reservation_id},
                    {"$set": {"status": "Cancelled"}}
                )
                print(f"Update result - Modified count: {result.modified_count}", file=sys.stderr)

                # If no modification happened, the reservation wasn't updated
                if result.modified_count == 0:
                    flash("Failed to cancel the reservation (no update applied).", "danger")
                    return redirect(url_for("manage_bus_reservations"))

                # Attempt to update the seats availability on the bus route
                route_id = reservation.get("route_id")
                seats = reservation.get("seats")

                if route_id and seats:
                    print(f"Attempting to update available tickets for route: {route_id} by {seats} seats", file=sys.stderr)
                    
                    # Ensure available_tickets field exists and is updated correctly
                    seat_update = mongo.db.bus_routes.update_one(
                        {"_id": ObjectId(route_id)},
                        {"$inc": {"available_tickets": int(seats)}}
                    )
                    print(f"Seats update result - Modified count: {seat_update.modified_count}", file=sys.stderr)
                    
                    # Check if the seat update succeeded
                    if seat_update.modified_count == 0:
                        flash("Failed to update available seats on the bus route.", "danger")
                        return redirect(url_for("manage_bus_reservations"))
                else:
                    print("Missing route_id or seats, skipping seat return.", file=sys.stderr)

                flash("Reservation cancelled and seats returned to availability.", "success")
            else:
                flash("This reservation is already cancelled.", "warning")
        else:
            flash("Reservation not found.", "warning")
            
    except Exception as e:
        print(f"Exception occurred: {e}", file=sys.stderr)
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for("manage_bus_reservations"))




#### CAR USER #######
# Route to choose transportation
@app.route("/choose-transportation")
def choose_transportation():
    return render_template("choose_transportation.html")

# Route to view available car routes
@app.route("/available-cars")
def show_available_cars():
    today = datetime.today()
    
    # Fetching car routes where the date is greater than or equal to today
    car_routes = list(mongo.db.car_routes.find({"date": {"$gte": today}}))

    # Formatting date and converting ObjectId to string for display
    for route in car_routes:
        route["_id"] = str(route["_id"])
        route["formatted_date"] = route["date"].strftime("%Y-%m-%d")

    return render_template("user/available_car_routes.html", routes=car_routes)

# Route to book a car
@app.route("/book-car/<route_id>", methods=["GET", "POST"])
def book_car(route_id):
    route = mongo.db.car_routes.find_one({"_id": ObjectId(route_id)})
    
    if not route:
        flash("Car route not found.", "danger")
        return redirect(url_for("show_available_cars"))

    if request.method == "POST":
        name = request.form.get("name")
        start_time = request.form.get("start_time")
        people = request.form.get("people")
        nid = request.form.get("nid")
        note = request.form.get("note")

        if not all([name, start_time, people, nid]):
            flash("Please fill in all required fields.", "danger")
            return redirect(request.url)

        # Create a new order in the car_orders collection
        order_data = {
            "route_id": ObjectId(route_id),
            "user_id": session.get('user_id'),  # Store user ID for referencing in admin view
            "name": name,
            "preferred_start_time": start_time,
            "people": int(people),
            "nid": nid,
            "note": note,
            "status": "pending",  # Set initial status to "pending"
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            # Store route details to ensure bill view has necessary information
            "origin": route.get("origin"),
            "destination": route.get("destination"),
            "fare": route.get("fare"),
            "date": route.get("date"),
        }

        # Insert the new order into car_orders collection
        mongo.db.car_orders.insert_one(order_data)

        # Update the car route's available cars
        mongo.db.car_routes.update_one(
            {"_id": ObjectId(route_id)},
            {"$inc": {"available_cars": -1}}
        )

        flash("Car booking successful!", "success")
        return redirect(url_for("show_available_cars"))

    return render_template("user/book_car.html", route=route)

# Admin - View All Orders
@app.route('/admin/car_reservations')
def admin_car_reservations():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    
    # Retrieve all orders from car_orders collection
    orders = mongo.db.car_orders.find()
    return render_template('admin/car_reservation.html', orders=orders)


# Admin - Approve Order
@app.route('/admin/approve_order/<order_id>')
def approve_order(order_id):
    try:
        # Find the order using order_id
        order = mongo.db.car_orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            flash("Order not found.", "danger")
            return redirect(url_for('admin_car_reservations'))
        
        # Update the order status to 'approved'
        mongo.db.car_orders.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "approved", "confirmed_at": datetime.utcnow()}}
        )
        flash("Order Approved!", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    
    return redirect(url_for('admin_car_reservations'))


# Admin - Cancel Order
@app.route('/admin/cancel_order/<order_id>')
def cancel_order(order_id):
    try:
        # Find the order using order_id
        order = mongo.db.car_orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            flash("Order not found.", "danger")
            return redirect(url_for('admin_car_reservations'))
        
        # Update the order status to 'rejected'
        mongo.db.car_orders.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "rejected"}}
        )
        flash("Order Canceled!", "danger")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    
    return redirect(url_for('admin_car_reservations'))



@app.route('/bill/<order_id>')
def view_bill(order_id):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    order = mongo.db.car_orders.find_one({'_id': ObjectId(order_id)})

    if order and order['status'] == 'approved':
        route = mongo.db.car_routes.find_one({'_id': ObjectId(order['route_id'])})

        if route:
            return render_template('user/bill.html', order=order, route=route)
        else:
            flash("Associated car route not found.", "danger")
            return redirect(url_for('my_orders'))

    flash("Unauthorized or Unapproved Order", "danger")
    return redirect(url_for('my_orders'))

@app.route("/my-orders")
def my_orders():
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    # Fetch orders and convert cursor to a list
    orders_cursor = mongo.db.car_orders.find({"user_id": session.get('user_id')})
    orders = list(orders_cursor)  # Convert the cursor to a list

    # Add formatted_date field to each order if the date exists
    for order in orders:
        if "date" in order:
            order["formatted_date"] = order["date"].strftime("%Y-%m-%d")  # Format the date as needed
        else:
            order["formatted_date"] = "N/A"  # Default value if date is missing
    
    return render_template("user/my_orders.html", orders=orders)
#################

@app.route("/user/chat", methods=["GET", "POST"])
def user_chat():
    if "user_id" not in session:
        flash("Please log in to chat.", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    if request.method == "POST":
        message = request.form.get("message")
        if message:
            mongo.db.chats.insert_one({
                "sender": "user",
                "user_id": user_id,
                "message": message,
                "timestamp": datetime.utcnow()
            })
        return redirect(url_for("user_chat"))

    messages = mongo.db.chats.find({"user_id": user_id}).sort("timestamp", 1)
    return render_template("user/chat.html", messages=messages)

@app.route("/admin/messages")
def admin_messages():
    if "admin_id" not in session:
        flash("Admin login required.", "danger")
        return redirect(url_for("admin_login"))

    user_ids = mongo.db.chats.distinct("user_id")
    user_list = []
    for uid in user_ids:
        last = mongo.db.chats.find({"user_id": uid}).sort("timestamp", -1).limit(1)[0]
        user = mongo.db.users.find_one({"_id": ObjectId(uid)})
        user_list.append({
            "user_id": uid,
            "username": user["username"] if user else "Unknown",
            "last_message": last["message"],
            "timestamp": last["timestamp"]
        })

    return render_template("admin/messages.html", users=user_list)

@app.route("/admin/chat/<user_id>", methods=["GET", "POST"])
def admin_chat(user_id):
    if "admin_id" not in session:
        flash("Admin login required.", "danger")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        message = request.form.get("message")
        if message:
            mongo.db.chats.insert_one({
                "sender": "admin",
                "user_id": user_id,
                "message": message,
                "timestamp": datetime.utcnow()
            })
        return redirect(url_for("admin_chat", user_id=user_id))

    messages = mongo.db.chats.find({"user_id": user_id}).sort("timestamp", 1)
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    username = user["username"] if user else "Unknown User"
    return render_template("admin/chat_view.html", messages=messages, username=username)
# Run the App
if __name__ == "__main__":
    app.run(debug=True, port=8800)
