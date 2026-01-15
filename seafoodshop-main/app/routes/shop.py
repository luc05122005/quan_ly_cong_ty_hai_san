# app/routes/shop.py
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from bson import ObjectId
from datetime import datetime
from math import ceil
from app.db import products_collection, cart_collection, invoices_collection, users_collection

shop_bp = Blueprint("shop", __name__)


# =========================
# --- DANH SÁCH SẢN PHẨM ---
# =========================
@shop_bp.route("/products")
def products():
    category = request.args.get("category")
    sort = request.args.get("sort")
    page = int(request.args.get("page", 1))
    per_page = 8

    query = {}
    if category:
        query["category"] = category

    sort_option = None
    if sort == "price_asc":
        sort_option = ("price", 1)
    elif sort == "price_desc":
        sort_option = ("price", -1)
    elif sort == "new":
        sort_option = ("created_at", -1)

    total_products = products_collection.count_documents(query)
    total_pages = ceil(total_products / per_page)
    skip = (page - 1) * per_page

    if sort_option:
        products = list(products_collection.find(query).sort([sort_option]).skip(skip).limit(per_page))
    else:
        products = list(products_collection.find(query).skip(skip).limit(per_page))

    return render_template(
        "shop/products.html",
        products=products,
        total_pages=total_pages,
        page=page,
        category=category,
        sort=sort
    )


# =========================
# --- THÊM SẢN PHẨM VÀO GIỎ HÀNG ---
# =========================
@shop_bp.route("/cart/add/<product_id>")
def add_to_cart(product_id):
    if not session.get("user_id"):
        flash("Vui lòng đăng nhập để thêm sản phẩm!", "warning")
        return redirect(url_for("auth.login"))

    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if product:
        cart_item = {
            "user_id": ObjectId(session["user_id"]),
            "product_id": product["_id"],
            "name": product["name"],
            "price": product["price"],
            "image": product.get("image"),
            "quantity": 1,
            "added_at": datetime.now()
        }

        existing = cart_collection.find_one({
            "user_id": ObjectId(session["user_id"]),
            "product_id": product["_id"]
        })
        if existing:
            cart_collection.update_one(
                {"_id": existing["_id"]},
                {"$inc": {"quantity": 1}, "$set": {"added_at": datetime.now()}}
            )
        else:
            cart_collection.insert_one(cart_item)

    return redirect(url_for("shop.cart"))


# =========================
# --- XEM GIỎ HÀNG ---
# =========================
@shop_bp.route("/cart")
def cart():
    if not session.get("user_id"):
        flash("Vui lòng đăng nhập để xem giỏ hàng!", "warning")
        return redirect(url_for("auth.login"))

    user_cart = list(cart_collection.find({"user_id": ObjectId(session["user_id"])}))
    total = sum(item["price"] * item["quantity"] for item in user_cart)
    return render_template("shop/cart.html", cart=user_cart, total=total)


# =========================
# --- XÓA SẢN PHẨM KHỎI GIỎ ---
# =========================
@shop_bp.route("/cart/remove/<cart_id>")
def remove_from_cart(cart_id):
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    cart_collection.delete_one({"_id": ObjectId(cart_id), "user_id": ObjectId(session["user_id"])})
    flash("Đã xóa sản phẩm khỏi giỏ hàng.", "success")
    return redirect(url_for("shop.cart"))


@shop_bp.route("/cart/update/<cart_id>", methods=["POST"])
def update_cart_quantity(cart_id):
    if not session.get("user_id"):
        return {"status": "error", "message": "Not logged in"}, 403

    data = request.get_json()
    quantity = float(data.get("quantity", 1))

    cart_collection.update_one(
        {"_id": ObjectId(cart_id), "user_id": ObjectId(session["user_id"])},
        {"$set": {"quantity": quantity}}
    )
    return jsonify({"status": "success"}) # type: ignore


# =========================
# --- CHECKOUT / TẠO HÓA ĐƠN ---
# =========================
@shop_bp.route("/cart/checkout", methods=["POST"])
def checkout():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    address = request.form.get("address")  # --- FIX ---
    payment_method = request.form.get("payment_method")  # --- FIX ---

    user_cart = list(cart_collection.find({"user_id": ObjectId(session["user_id"])}))
    if not user_cart:
        flash("Giỏ hàng của bạn đang trống!", "warning")
        return redirect(url_for("shop.cart"))

    invoice = {
        "user_id": ObjectId(session["user_id"]),
        "products": [{
            "product_id": item["product_id"],
            "name": item["name"],
            "price": item["price"],
            "quantity": item["quantity"]
        } for item in user_cart],
        "total": sum(item["price"] * item["quantity"] for item in user_cart),
        "address": address,  # --- FIX ---
        "payment_method": payment_method,  # --- FIX ---
        "created_at": datetime.now()
    }

    invoices_collection.insert_one(invoice)
    cart_collection.delete_many({"user_id": ObjectId(session["user_id"])})

    return render_template("shop/checkout_success.html", invoice=invoice)


# =========================
# --- LỊCH SỬ MUA HÀNG KHÁCH HÀNG ---
# =========================
@shop_bp.route("/history")
def history():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    invoices = list(invoices_collection.find({"user_id": ObjectId(session["user_id"])}).sort("created_at", -1))

    return render_template("shop/history.html", invoices=invoices)

@shop_bp.route("/search")
def search():
    keyword = request.args.get("q", "").strip()

    if not keyword:
        return redirect(url_for("shop.products"))

    # Tìm sản phẩm theo nhiều trường: name, category, description
    results = list(products_collection.find({
        "$or": [
            {"name": {"$regex": keyword, "$options": "i"}},
            {"category": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}}
        ]
    }))

    return render_template(
        "shop/search_results.html",
        keyword=keyword,
        results=results
    )
@shop_bp.route("/product/<product_id>")
def view_product(product_id):
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    if not product:
        flash("Sản phẩm không tồn tại", "warning")
        return redirect(url_for("shop.products"))
    
    # Lấy category của sản phẩm
    category = product.get("category")
    # Chuyển hướng tới trang danh mục với category đã chọn
    return redirect(url_for("shop.products", category=category))




