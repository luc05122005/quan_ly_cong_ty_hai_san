from flask import Blueprint, render_template
from app.db import products_collection  # import collection từ db.py

# Blueprint cho các route chính
main_bp = Blueprint(
    "main", 
    __name__, 
    template_folder="../templates"  # đường dẫn từ routes/main.py đến templates
)

# Trang chủ
@main_bp.route("/")
def home():
    return render_template("home.html")

# Trang giới thiệu
@main_bp.route("/gioithieu")
def gioithieu():
    return render_template("gioithieu.html")

# Trang liên hệ
@main_bp.route("/lienhe")
def lienhe():
    return render_template("lienhe.html")

# 🌊 Trang sản phẩm
@main_bp.route("/products")
def products():
    # Lấy tất cả sản phẩm từ MongoDB
    products = list(products_collection.find())
    return render_template("products.html", products=products)
