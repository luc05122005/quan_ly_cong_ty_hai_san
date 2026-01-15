from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import users_collection, bcrypt
from bson import ObjectId

auth_bp = Blueprint("auth", __name__)

# -----------------------------
# ĐĂNG NHẬP
# -----------------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = users_collection.find_one({"username": username})
        if user and bcrypt.check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["username"] = user["username"]
            session["role"] = user.get("role", "customer")
            flash(f"Chào mừng {user.get('fullname', username)} quay lại!", "success")

            if session["role"] == "admin":
                return redirect(url_for("admin.dashboard"))
            else:
                return redirect(url_for("main.home"))
        else:
            flash("❌ Sai tên đăng nhập hoặc mật khẩu!", "danger")

    return render_template("auth/login.html")

# -----------------------------
# ĐĂNG KÝ
# -----------------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname")
        phone = request.form.get("phone")
        email = request.form.get("email")
        address = request.form.get("address")
        username = request.form.get("username")
        password = request.form.get("password")

        if users_collection.find_one({"username": username}):
            flash("⚠️ Tên đăng nhập đã tồn tại!", "warning")
            return redirect(url_for("auth.register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        users_collection.insert_one({
            "fullname": fullname,
            "phone": phone,
            "email": email,
            "address": address,
            "username": username,
            "password": hashed_password,
            "role": "customer"
        })

        flash("✅ Đăng ký thành công! Hãy đăng nhập.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

# -----------------------------
# ĐĂNG GUAT
# -----------------------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("main.home"))
