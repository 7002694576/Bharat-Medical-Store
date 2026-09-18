from flask import Flask, render_template, request, jsonify, redirect
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)


# =========================================================
# MONGODB
# =========================================================

# Render par MONGO_URI environment variable se Atlas connect hoga.
# Local PC par agar MONGO_URI nahi hai to local MongoDB use hoga.

import os
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["Bharat_Battery_DB"]

orders_collection = db["orders"]
products_collection = db["products"]


# =========================================================
# IMAGE UPLOAD
# =========================================================

UPLOAD_FOLDER = "static/uploads"

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# HOME PAGE
# =========================================================

@app.route("/")
def home():

    products = list(
        products_collection.find().sort("_id", -1)
    )

    return render_template(
        "index.html",
        products=products
    )


# =========================================================
# ADMIN PAGE
# =========================================================

@app.route("/admin")
def admin():

    products = list(
        products_collection.find().sort("_id", -1)
    )

    orders = list(
        orders_collection.find().sort("_id", -1)
    )

    total_orders = orders_collection.count_documents({})

    pending_orders = orders_collection.count_documents({
        "status": "Pending"
    })

    total_products = products_collection.count_documents({})

    return render_template(
        "admin.html",
        products=products,
        orders=orders,
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_products=total_products
    )


# =========================================================
# ADD / EDIT PRODUCT
# =========================================================

@app.route("/admin/save-product", methods=["POST"])
def save_product():

    try:

        product_id = request.form.get("product_id")

        old_image = request.form.get("old_image", "")

        category = request.form.get(
            "category",
            ""
        ).strip()

        name = request.form.get(
            "name",
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


        # -------------------------------------------------
        # IMAGE
        # -------------------------------------------------

        image_path = old_image

        if "image" in request.files:

            file = request.files["image"]

            if file and file.filename:

                if allowed_file(file.filename):

                    filename = secure_filename(
                        file.filename
                    )

                    file.save(
                        os.path.join(
                            app.config["UPLOAD_FOLDER"],
                            filename
                        )
                    )

                    image_path = (
                        "uploads/" + filename
                    )


        # -------------------------------------------------
        # PRODUCT DATA
        # -------------------------------------------------

        product_data = {

            "category": category,

            "name": name,

            "capacity": capacity,

            "price": price,

            "warranty": warranty,

            "image": image_path,

            "updated_at": datetime.now()
        }


        # -------------------------------------------------
        # EDIT
        # -------------------------------------------------

        if product_id:

            products_collection.update_one(

                {
                    "_id": ObjectId(product_id)
                },

                {
                    "$set": product_data
                }
            )


        # -------------------------------------------------
        # ADD
        # -------------------------------------------------

        else:

            product_data["created_at"] = datetime.now()

            products_collection.insert_one(
                product_data
            )


        return redirect("/admin")


    except Exception as e:

        return f"Product Save Error: {e}"


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.route(
    "/admin/delete-product/<product_id>",
    methods=["POST"]
)
def delete_product(product_id):

    try:

        products_collection.delete_one(
            {
                "_id": ObjectId(product_id)
            }
        )

        return redirect("/admin")


    except Exception as e:

        return f"Product Delete Error: {e}"


# =========================================================
# PLACE ORDER
# =========================================================

@app.route("/place-order", methods=["POST"])
def place_order():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No order data received"
            })


        product = data.get(
            "product",
            ""
        )

        name = data.get(
            "name",
            ""
        )

        mobile = data.get(
            "mobile",
            ""
        )

        address = data.get(
            "address",
            ""
        )

        price = data.get(
            "price",
            ""
        )


        order_data = {

            "product": product,

            "name": name,

            "mobile": mobile,

            "address": address,

            "price": price,

            "status": "Pending",

            "order_date": datetime.now(),

            "status_updated_at": datetime.now()
        }


        orders_collection.insert_one(
            order_data
        )


        return jsonify({

            "success": True,

            "message": "Order placed successfully"

        })


    except Exception as e:

        return jsonify({

            "success": False,

            "message": str(e)

        })


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

@app.route(
    "/admin/update-order-status/<order_id>",
    methods=["POST"]
)
def update_order_status(order_id):

    try:

        status = request.form.get(
            "status",
            "Pending"
        )


        allowed_statuses = [

            "Pending",

            "Confirmed",

            "Delivered",

            "Cancelled"

        ]


        if status not in allowed_statuses:

            return "Invalid Order Status"


        orders_collection.update_one(

            {
                "_id": ObjectId(order_id)
            },

            {
                "$set": {

                    "status": status,

                    "status_updated_at":
                        datetime.now()

                }
            }
        )


        return redirect("/admin")


    except Exception as e:

        return f"Order Status Update Error: {e}"


# =========================================================
# DELETE ORDER
# =========================================================

@app.route(
    "/admin/delete-order/<order_id>",
    methods=["POST"]
)
def delete_order(order_id):

    try:

        orders_collection.delete_one(

            {
                "_id": ObjectId(order_id)
            }

        )

        return redirect("/admin")


    except Exception as e:

        return f"Order Delete Error: {e}"


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
# RUN LOCAL
# =========================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),

        debug=True

    )
