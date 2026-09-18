from flask import Flask, render_template, request, redirect
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)

# =========================
# MONGODB
# =========================

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017/"
)

client = MongoClient(MONGO_URI)

db = client["Bharat_Medical_Store"]

medicines_collection = db["medicines"]


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():

    medicines = list(
        medicines_collection.find()
    )

    return render_template(
        "index.html",
        medicines=medicines
    )


# =========================
# ADMIN PANEL
# =========================

@app.route("/admin")
def admin():

    medicines = list(
        medicines_collection.find()
    )

    return render_template(
        "admin.html",
        medicines=medicines
    )


# =========================
# ADD MEDICINE
# =========================

@app.route("/add-medicine", methods=["POST"])
def add_medicine():

    name = request.form["name"]

    description = request.form["description"]

    price = float(
        request.form["price"]
    )

    stock = int(
        request.form["stock"]
    )

    medicines_collection.insert_one({

        "name": name,

        "description": description,

        "price": price,

        "stock": stock

    })

    return redirect("/admin")


# =========================
# DELETE MEDICINE
# =========================

@app.route(
    "/delete-medicine/<medicine_id>",
    methods=["POST"]
)
def delete_medicine(medicine_id):

    medicines_collection.delete_one({

        "_id": ObjectId(medicine_id)

    })

    return redirect("/admin")


# =========================
# RUN APP
# =========================

if __name__ == "__main__":

    app.run(
        debug=True
    )
