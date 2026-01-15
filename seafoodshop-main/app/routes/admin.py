from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.db import products_collection, invoices_collection, stock_collection, users_collection
from bson import ObjectId
from bson.son import SON
from datetime import datetime
from flask import request
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ============================
# 0. DASHBOARD
# ============================
@admin_bp.route("/dashboard")
def dashboard():
    total_users = users_collection.count_documents({})
    total_products = products_collection.count_documents({})
    total_invoices = invoices_collection.count_documents({})
    total_stock = stock_collection.count_documents({})

    return render_template("admin/dashboard.html",
                           total_users=total_users,
                           total_products=total_products,
                           total_invoices=total_invoices,
                           total_stock=total_stock)


# ------------------------
# DANH SÁCH HÓA ĐƠN + BIỂU ĐỒ DOANH THU
# ------------------------
@admin_bp.route("/invoices")
def invoices():
    query = {}
    user_id = request.args.get("user_id")   # thay customer_id → user_id
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    period_type = request.args.get("period_type", "day")

    # Lọc theo user
    if user_id:
        query["user_id"] = ObjectId(user_id)

    # Lọc theo ngày
    if start_date and end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        query["created_at"] = {"$gte": start, "$lte": end}

    # Lấy danh sách hóa đơn
    invoices_list = list(invoices_collection.find(query))

    # Thêm thông tin user và tổng tiền từng hóa đơn
    for inv in invoices_list:
        user = users_collection.find_one({"_id": ObjectId(inv["user_id"])})
        inv["user_name"] = user["fullname"] if user else "Unknown"

        products = []
        for item in inv.get("products", []):
            prod = products_collection.find_one({"_id": ObjectId(item["product_id"])})
            if prod:
                products.append({
                    "name": prod["name"],
                    "price": prod["price"],
                    "quantity": item["quantity"],
                    "total": prod["price"] * item["quantity"]
                })
        inv["products"] = products
        inv["total_amount"] = sum(p["total"] for p in products)

    # ------------------------
    # TÍNH DỮ LIỆU BIỂU ĐỒ DOANH THU
    # ------------------------
    pipeline = []

    if period_type == "day":
        group_id = {"year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                    "day": {"$dayOfMonth": "$created_at"}}
    elif period_type == "month":
        group_id = {"year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"}}
    elif period_type == "quarter":
        group_id = {"year": {"$year": "$created_at"},
                    "quarter": {"$ceil": {"$divide": [{"$month": "$created_at"}, 3]}}}
    elif period_type == "year":
        group_id = {"year": {"$year": "$created_at"}}
    else:
        group_id = None

    if group_id:
        pipeline.append({"$match": query})
        pipeline.append({"$group": {"_id": group_id, "total_amount": {"$sum": "$total_amount"}}})
        pipeline.append({"$sort": SON([("_id.year", 1), ("_id.month", 1), ("_id.day", 1)])})

    chart_data_raw = list(invoices_collection.aggregate(pipeline))
    chart_labels = []
    chart_data = []

    for item in chart_data_raw:
        id_ = item["_id"]
        if period_type == "day":
            label = f"{id_['day']}/{id_['month']}/{id_['year']}"
        elif period_type == "month":
            label = f"{id_['month']}/{id_['year']}"
        elif period_type == "quarter":
            label = f"Q{id_['quarter']} {id_['year']}"
        elif period_type == "year":
            label = str(id_['year'])
        chart_labels.append(label)
        chart_data.append(item["total_amount"])

    # Lấy danh sách user cho dropdown
    users_list = list(users_collection.find({}))

    return render_template("admin/invoices.html",
                           invoices=invoices_list,
                           chart_labels=chart_labels,
                           chart_data=chart_data,
                           users_list=users_list,
                           selected_user=user_id,
                           start_date=start_date,
                           end_date=end_date, 
                           period_type=period_type)
                           
# ------------------------
# Xem chi tiết hóa đơn
# ------------------------
@admin_bp.route("/invoices/view/<invoice_id>")
def view_invoice(invoice_id):
    invoice = invoices_collection.find_one({"_id": ObjectId(invoice_id)})
    if not invoice:
        flash("Hóa đơn không tồn tại!", "danger")
        return redirect(url_for("admin.invoices"))

    user = users_collection.find_one({"_id": ObjectId(invoice["user_id"])})
    invoice["user_name"] = user["fullname"] if user else "Unknown"

    products = []
    for item in invoice.get("products", []):
        prod = products_collection.find_one({"_id": ObjectId(item["product_id"])})
        if prod:
            products.append({
                "name": prod["name"],
                "price": prod["price"],
                "quantity": item["quantity"],
                "total": prod["price"] * item["quantity"]
            })
    invoice["products"] = products
    invoice["total_amount"] = sum(p["total"] for p in products)

    return render_template("admin/view_invoice.html", invoice=invoice)

# ------------------------
# Xóa hóa đơn
# ------------------------
@admin_bp.route("/invoices/delete/<invoice_id>", methods=["POST"])
def delete_invoice(invoice_id):
    invoices_collection.delete_one({"_id": ObjectId(invoice_id)})
    flash("Xóa hóa đơn thành công!", "success")
    return redirect(url_for("admin.invoices"))

# ------------------------
# Sửa trạng thái hóa đơn
# ------------------------
@admin_bp.route("/invoices/edit/<invoice_id>", methods=["GET", "POST"])
def edit_invoice(invoice_id):
    invoice = invoices_collection.find_one({"_id": ObjectId(invoice_id)})

    if request.method == "POST":
        status = request.form["status"]
        invoices_collection.update_one({"_id": ObjectId(invoice_id)}, {"$set": {"status": status}})
        flash("Cập nhật hóa đơn thành công!", "success")
        return redirect(url_for("admin.invoices"))

    return render_template("admin/edit_invoice.html", invoice=invoice)
# ============================
# 2. QUẢN LÝ SẢN PHẨM
# ============================
@admin_bp.route("/products")
def products():
    all_products = products_collection.find()
    return render_template("admin/products.html", products=all_products)


@admin_bp.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":

        name = request.form["name"]
        price = float(request.form["price"])
        stock = int(request.form["stock"])
        category = request.form.get("category", "")
        image_url = request.form.get("image", "")  # ví dụ lấy từ form

        # 1) Link ảnh URL
        image_url = request.form.get("image_url", "").strip()

        # 2) File upload
        image = request.files.get("image")
        image_filename = ""

        if image and image.filename != "":
            image_filename = image.filename
            image_path = f"static/uploads/{image_filename}"
            image.save(image_path)
            final_image = image_filename
        else:
            final_image = image_url   # dùng link URL nếu không upload file

        # Luôn có final_image
        products_collection.insert_one({
            "name": name,
            "price": price,
            "stock": stock,
            "category": category,
            "image": final_image
        })
        

        flash("Thêm sản phẩm thành công!", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/add_product.html")



@admin_bp.route("/products/edit/<product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    product = products_collection.find_one({"_id": ObjectId(product_id)})

    if request.method == "POST":
        name = request.form.get("name", product.get("name"))
        price = float(request.form.get("price", product.get("price", 0)))
        stock = int(request.form.get("stock", product.get("stock", 0)))
        category = request.form.get("category", product.get("category", ""))

        # 1) Lấy link URL từ form
        image_url = request.form.get("image_url", "").strip()

        # 2) Xử lý file upload
        image = request.files.get("image")
        if image and image.filename != "":
            image_path = f"static/uploads/{image.filename}"
            image.save(image_path)
            final_image = image.filename
        else:
            # nếu không upload file, dùng link URL hoặc giữ nguyên ảnh cũ
            final_image = image_url if image_url else product.get("image", "")

        # Cập nhật vào MongoDB
        products_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {
                "name": name,
                "price": price,
                "stock": stock,
                "category": category,
                "image": final_image
            }}
        )

        flash("Cập nhật sản phẩm thành công!", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/edit_product.html", product=product)


@admin_bp.route("/products/delete/<product_id>")
def delete_product(product_id):
    products_collection.delete_one({"_id": ObjectId(product_id)})
    flash("Xóa sản phẩm thành công!", "success")
    return redirect(url_for("admin.products"))


# ============================
# 3. QUẢN LÝ KHO (XUẤT – NHẬP – TỒN)

# ============================

@admin_bp.route("/stock")
def stock_list():
    stock_list = list(stock_collection.find().sort("created_at", -1))

    # Lấy danh sách sản phẩm để có tồn kho
    products = {str(p["_id"]): p for p in products_collection.find()}

    # Gán thêm tồn kho vào từng dòng lịch sử
    for s in stock_list:
        product_id = str(s["product_id"])
        s["current_stock"] = products.get(product_id, {}).get("stock", 0)

    return render_template("admin/stock.html", stock_list=stock_list)

@admin_bp.route("/stock")
def stock():
    all_stock = stock_collection.find()
    products = products_collection.find()
    return render_template("admin/stock.html", stock=all_stock, products=products)


@admin_bp.route("/stock/add", methods=["GET", "POST"])
def add_stock():
    if request.method == "POST":

        product_id = request.form["product_id"]
        quantity = int(request.form["quantity"])
        action = request.form["action"]  # nhập hoặc xuất

        stock_collection.insert_one({
            "product_id": ObjectId(product_id),
            "quantity": quantity,
            "action": action,
            "date": datetime.now()
        })

        # Cập nhật tồn kho
        product = products_collection.find_one({"_id": ObjectId(product_id)})

        new_quantity = product["quantity"] + quantity if action == "nhap" else product["quantity"] - quantity

        products_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"quantity": new_quantity}}
        )

        flash("Ghi nhận kho thành công!", "success")
        return redirect(url_for("admin.stock"))

    products = products_collection.find()
    return render_template("admin/add_stock.html", products=products)


@admin_bp.route("/stock/delete/<stock_id>")
def delete_stock(stock_id):
    stock_collection.delete_one({"_id": ObjectId(stock_id)})
    flash("Xóa dòng ghi nhận kho thành công!", "success")
    return redirect(url_for("admin.stock"))
