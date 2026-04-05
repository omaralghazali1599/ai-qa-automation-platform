from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)
app.secret_key = "thesis-secret-key"

bookings = {}
booking_counter = [1]
VALID_STATUSES = ["pending", "confirmed", "cancelled"]

def next_id():
    bid = booking_counter[0]
    booking_counter[0] += 1
    return bid

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

@app.route("/bookings", methods=["POST"])
def create_booking():
    data = request.get_json()
    guest_name = data.get("guest_name", "").strip()
    room_type = data.get("room_type", "").strip()
    check_in = data.get("check_in", "")
    check_out = data.get("check_out", "")
    guests = data.get("guests", 1)

    if not guest_name or not room_type or not check_in or not check_out:
        return jsonify({"error": "All fields are required"}), 400

    check_in_dt = parse_date(check_in)
    check_out_dt = parse_date(check_out)

    if not check_in_dt or not check_out_dt:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    if check_out_dt <= check_in_dt:
        return jsonify({"error": "Check-out must be after check-in"}), 400
    if not isinstance(guests, int) or guests < 1:
        return jsonify({"error": "Guests must be a positive integer"}), 400
    if guests > 10:
        return jsonify({"error": "Maximum 10 guests per booking"}), 400

    bid = next_id()
    bookings[bid] = {
        "id": bid,
        "guest_name": guest_name,
        "room_type": room_type,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "status": "pending"
    }
    return jsonify(bookings[bid]), 201


@app.route("/bookings", methods=["GET"])
def list_bookings():
    status = request.args.get("status")
    result = list(bookings.values())
    if status:
        if status not in VALID_STATUSES:
            return jsonify({"error": f"Status must be one of {VALID_STATUSES}"}), 400
        result = [b for b in result if b["status"] == status]
    return jsonify(result), 200


@app.route("/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    if booking_id not in bookings:
        return jsonify({"error": "Booking not found"}), 404
    return jsonify(bookings[booking_id]), 200


@app.route("/bookings/<int:booking_id>/confirm", methods=["POST"])
def confirm_booking(booking_id):
    if booking_id not in bookings:
        return jsonify({"error": "Booking not found"}), 404
    if bookings[booking_id]["status"] == "cancelled":
        return jsonify({"error": "Cannot confirm a cancelled booking"}), 400
    bookings[booking_id]["status"] = "confirmed"
    return jsonify({"message": "Booking confirmed", "booking": bookings[booking_id]}), 200


@app.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
def cancel_booking(booking_id):
    if booking_id not in bookings:
        return jsonify({"error": "Booking not found"}), 404
    if bookings[booking_id]["status"] == "cancelled":
        return jsonify({"error": "Booking is already cancelled"}), 400
    bookings[booking_id]["status"] = "cancelled"
    return jsonify({"message": "Booking cancelled", "booking": bookings[booking_id]}), 200


@app.route("/bookings/<int:booking_id>", methods=["DELETE"])
def delete_booking(booking_id):
    if booking_id not in bookings:
        return jsonify({"error": "Booking not found"}), 404
    if bookings[booking_id]["status"] == "confirmed":
        return jsonify({"error": "Cannot delete a confirmed booking"}), 400
    deleted = bookings.pop(booking_id)
    return jsonify({"message": "Booking deleted", "booking": deleted}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5003)