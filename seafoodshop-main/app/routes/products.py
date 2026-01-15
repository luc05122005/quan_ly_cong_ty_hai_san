from flask import Blueprint, render_template, request
from app.db import products_collection

products_bp = Blueprint("products", __name__)

@products_bp.route("/san-pham")
def product_list():

    # --- Lấy tham số lọc ---
    category = request.args.get("loai")  # vd: tom, cua, oc
    min_price = request.args.get("min")
    max_price = request.args.get("max")

    # --- Điều kiện truy vấn Mongo ---
    query = {}

    if category:
        query["category"] = category

    if min_price or max_price:
        query["price"] = {}
        if min_price:
            query["price"]["$gte"] = int(min_price)
        if max_price:
            query["price"]["$lte"] = int(max_price)

    # --- Lấy dữ liệu ---
    products = list(products_collection.find(query))

    return render_template("product_list.html", products=products, category=category)
