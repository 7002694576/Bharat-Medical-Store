from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os
from datetime import datetime

app = Flask(__name__)

# =========================================================
# MONGODB CONFIGURATION
# =========================================================

MONGO_URI = os.environ.get("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI environment variable is missing")

client = None
db = None
orders_collection = None
products_collection = None


def get_database():

    global client
    global db
    global orders_collection
    global products_collection

    if client is None:

        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )

        db = client["Bharat_Battery_DB"]

        orders_collection = db["orders"]
        products_collection = db["products"]

    return db


# =========================================================
# UPLOAD SETTINGS
# =========================================================

UPLOAD_FOLDER = "static/uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    get_database()

    products = list(
        products_collection.find().sort("_id", -1)
    )

    return render_template(
        "index.html",
        products=products
    )


# =========================================================
# ADMIN
# =========================================================

@app.route("/admin")
def admin():

    get_database()

    products = list(
        products_collection.find().sort("_id", -1)
    )

    orders = list(
        orders_collection.find().sort("_id", -1)
    )

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

    get_database()

    name = request.form.get(
        "name",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    capacity = request.form.get(
        "capacity",
        ""
    ).strip()

    price = request.form.get(
        "price",
        ""
    ).strip()

    warranty = request.form.get(
        "warranty",
        ""
    ).strip()

    image = request.files.get("image")

    image_name = ""

    if image and image.filename:

        filename = secure_filename(
            image.filename
        )

        filepath = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        image.save(filepath)

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

    products_collection.insert_one(
        product
    )

    return redirect(
        url_for("admin")
    )


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.route("/delete_product/<product_id>")
def delete_product(product_id):

    get_database()

    try:

        products_collection.delete_one(
            {
                "_id": ObjectId(product_id)
            }
        )

    except Exception as e:

        print(
            "Delete Product Error:",
            e
        )

    return redirect(
        url_for("admin")
    )


# =========================================================
# EDIT PRODUCT
# =========================================================

@app.route(
    "/edit_product/<product_id>",
    methods=["GET", "POST"]
)
def edit_product(product_id):

    get_database()

    try:

        product = products_collection.find_one(
            {
                "_id": ObjectId(product_id)
            }
        )

    except Exception:

        return "Invalid Product ID", 400

    if not product:

        return "Product not found", 404

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        capacity = request.form.get(
            "capacity",
            ""
        ).strip()

        price = request.form.get(
            "price",
            ""
        ).strip()

        warranty = request.form.get(
            "warranty",
            ""
        ).strip()

        update_data = {

            "name": name,

            "category": category,

            "capacity": capacity,

            "price": price,

            "warranty": warranty
        }

        image = request.files.get("image")

        if image and image.filename:

            filename = secure_filename(
                image.filename
            )

            filepath = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            image.save(filepath)

            update_data["image"] = (
                "uploads/" + filename
            )

        products_collection.update_one(

            {
                "_id": ObjectId(product_id)
            },

            {
                "$set": update_data
            }
        )

        return redirect(
            url_for("admin")
        )

    products = list(
        products_collection.find().sort(
            "_id",
            -1
        )
    )

    orders = list(
        orders_collection.find().sort(
            "_id",
            -1
        )
    )

    return render_template(

        "admin.html",

        products=products,

        orders=orders,

        edit_product=product
    )


# =========================================================
# PLACE ORDER
# =========================================================

@app.route(
    "/order",
    methods=["POST"]
)
def order():

    get_database()

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

    orders_collection.insert_one(
        order_data
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

@app.route(
    "/update_order/<order_id>",
    methods=["POST"]
)
def update_order(order_id):

    get_database()

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

            {
                "_id": ObjectId(order_id)
            },

            {
                "$set": {
                    "status": status
                }
            }
        )

    except Exception as e:

        print(
            "Update Order Error:",
            e
        )

    return redirect(
        url_for("admin")
    )


# =========================================================
# DELETE ORDER
# =========================================================

@app.route(
    "/delete_order/<order_id>"
)
def delete_order(order_id):

    get_database()

    try:

        orders_collection.delete_one(

            {
                "_id": ObjectId(order_id)
            }
        )

    except Exception as e:

        print(
            "Order Delete Error:",
            e
        )

    return redirect(
        url_for("admin")
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    try:

        get_database()

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

        get_database()

        client.admin.command("ping")

        product_count = (
            products_collection.count_documents({})
        )

        order_count = (
            orders_collection.count_documents({})
        )

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
# RUN LOCAL
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True
    )
