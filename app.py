from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)

# =========================================================
# MONGODB CONNECTION
# =========================================================

MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    # Local computer ke liye
    MONGO_URI = "mongodb://127.0.0.1:27017/"

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000
)

db = client["Bharat_Battery_DB"]

orders_collection = db["orders"]
products_collection = db["products"]


# =========================================================
# UPLOAD SETTINGS
# =========================================================

UPLOAD_FOLDER = "static/uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    products = list(products_collection.find().sort("_id", -1))

    return render_template(
        "index.html",
        products=products
    )


# =========================================================
# ADMIN PAGE
# =========================================================

@app.route("/admin")
def admin():

    products = list(products_collection.find().sort("_id", -1))

    orders = list(orders_collection.find().sort("_id", -1))

    return render_template(
        "admin.html",
        products=products,
        orders=orders
    )


# =========================================================
# ADD PRODUCT
# =========================================================

@app.route("/add_product", methods=["POST"])
def add_product():

    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    capacity = request.form.get("capacity", "").strip()
    price = request.form.get("price", "").strip()
    warranty = request.form.get("warranty", "").strip()

    image = request.files.get("image")

    image_name = ""

    if image and image.filename:

        filename = secure_filename(image.filename)

        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        image.save(image_path)

        image_name = "uploads/" + filename

    product = {
        "name": name,
        "category": category,
        "capacity": capacity,
        "price": price,
        "warranty": warranty,
        "image": image_name,
        "created_at": datetime.utcnow()
    }

    products_collection.insert_one(product)

    return redirect(url_for("admin"))


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.route("/delete_product/<product_id>")
def delete_product(product_id):

    from bson.objectid import ObjectId

    try:

        products_collection.delete_one(
            {"_id": ObjectId(product_id)}
        )

    except Exception as e:

        print("Delete Error:", e)

    return redirect(url_for("admin"))


# =========================================================
# EDIT PRODUCT
# =========================================================

@app.route("/edit_product/<product_id>", methods=["GET", "POST"])
def edit_product(product_id):

    from bson.objectid import ObjectId

    try:

        product = products_collection.find_one(
            {"_id": ObjectId(product_id)}
        )

    except Exception:

        return "Invalid Product ID", 400

    if not product:

        return "Product not found", 404

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        capacity = request.form.get("capacity", "").strip()
        price = request.form.get("price", "").strip()
        warranty = request.form.get("warranty", "").strip()

        update_data = {
            "name": name,
            "category": category,
            "capacity": capacity,
            "price": price,
            "warranty": warranty
        }

        image = request.files.get("image")

        if image and image.filename:

            filename = secure_filename(image.filename)

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            image.save(image_path)

            update_data["image"] = "uploads/" + filename

        products_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )

        return redirect(url_for("admin"))

    return render_template(
        "admin.html",
        products=list(products_collection.find().sort("_id", -1)),
        orders=list(orders_collection.find().sort("_id", -1)),
        edit_product=product
    )


# =========================================================
# PLACE ORDER
# =========================================================

@app.route("/order", methods=["POST"])
def order():

    customer_name = request.form.get(
        "customer_name",
        ""
    ).strip()

    mobile = request.form.get(
        "mobile",
        ""
    ).strip()

    address = request.form.get(
        "address",
        ""
    ).strip()

    product_name = request.form.get(
        "product_name",
        ""
    ).strip()

    quantity = request.form.get(
        "quantity",
        "1"
    ).strip()

    order_data = {

        "customer_name": customer_name,

        "mobile": mobile,

        "address": address,

        "product_name": product_name,

        "quantity": quantity,

        "status": "Pending",

        "created_at": datetime.utcnow()
    }

    orders_collection.insert_one(order_data)

    return redirect(url_for("home"))


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

@app.route("/update_order/<order_id>", methods=["POST"])
def update_order(order_id):

    from bson.objectid import ObjectId

    status = request.form.get(
        "status",
        "Pending"
    )

    allowed_status = [
        "Pending",
        "Confirmed",
        "Delivered",
        "Cancelled"
    ]

    if status not in allowed_status:

        status = "Pending"

    try:

        orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "status": status
                }
            }
        )

    except Exception as e:

        print("Order Update Error:", e)

    return redirect(url_for("admin"))


# =========================================================
# DELETE ORDER
# =========================================================

@app.route("/delete_order/<order_id>")
def delete_order(order_id):

    from bson.objectid import ObjectId

    try:

        orders_collection.delete_one(
            {"_id": ObjectId(order_id)}
        )

    except Exception as e:

        print("Order Delete Error:", e)

    return redirect(url_for("admin"))


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    try:

        client.admin.command("ping")

        return jsonify({
            "status": "OK",
            "database": "Connected"
        })

    except Exception as e:

        return jsonify({
            "status": "ERROR",
            "database": str(e)
        }), 500


# =========================================================
# DATABASE TEST
# =========================================================

@app.route("/db-test")
def db_test():

    try:

        client.admin.command("ping")

        product_count = products_collection.count_documents({})

        order_count = orders_collection.count_documents({})

        return jsonify({

            "status": "OK",

            "mongodb": "Connected",

            "database": "Bharat_Battery_DB",

            "products": product_count,

            "orders": order_count

        })

    except Exception as e:

        return jsonify({

            "status": "ERROR",

            "error": str(e)

        }), 500


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
