from pymongo import MongoClient
from flask_bcrypt import Bcrypt

# 🔑 Khởi tạo Bcrypt
bcrypt = Bcrypt()

# 🌐 Cấu hình DB
class Config:
    MONGO_URI = "mongodb://localhost:27017/"
    DB_NAME = "seafoodshop"

# 🔗 Kết nối MongoDB
client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

# 🌊 Collections
users_collection = db["users"]
products_collection = db["products"]
cart_collection = db["cart"]
invoices_collection = db["invoices"]
# 🔥 THÊM BẢNG QUẢN LÝ KHO
stock_collection = db["stock"]   # <--- QUAN TRỌNG NHẤT

# 🌱 --- Tạo dữ liệu sản phẩm mẫu ---
if products_collection.count_documents({}) == 0:
    products_collection.insert_many([
        {
            "name": "Tôm sú tươi",
            "price": 250000,
            "stock": 50,
            "image": "https://via.placeholder.com/300?text=Tom+Su",
            "created_at": None
        },
        {
            "name": "Cua Cà Mau",
            "price": 400000,
            "stock": 35,
            "image": "https://via.placeholder.com/300?text=Cua+Ca+Mau",
            "created_at": None
        },
        {
            "name": "Mực ống",
            "price": 220000,
            "stock": 40,
            "image": "https://via.placeholder.com/300?text=Muc+Ong",
            "created_at": None
        }
    ])
    print("✅ Đã tạo dữ liệu sản phẩm mẫu")

# 🌱 --- Tạo admin mặc định ---
if users_collection.count_documents({"role": "admin"}) == 0:
    hashed_password = bcrypt.generate_password_hash("admin123").decode("utf-8")
    users_collection.insert_one({
        "username": "admin",
        "password": hashed_password,
        "role": "admin",
        "fullname": "Quản trị viên",
        "email": "admin@seafoodshop.vn"
    })
    print("✅ Tạo admin mới: admin / admin123 (password đã hash)")

# 🔧 --- Fix admin cũ nếu password chưa hash ---
admin = users_collection.find_one({"username": "admin"})
if admin and not admin["password"].startswith("$2b$"):
    hashed = bcrypt.generate_password_hash("admin123").decode("utf-8")
    users_collection.update_one({"_id": admin["_id"]}, {"$set": {"password": hashed}})
    print("✅ Đã hash lại password admin cũ")
