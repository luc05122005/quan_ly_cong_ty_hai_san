from flask import Flask, session
from app.routes.auth import auth_bp
from app.routes.shop import shop_bp
from app.routes.admin import admin_bp
from app.routes.main import main_bp
from app.db import db, cart_collection
from bson import ObjectId

# ⚠️ thêm static_folder và template_folder
app = Flask(
    __name__,
    static_folder="app/static",
    template_folder="app/templates"
)

app.secret_key = "secretkey"

# --------------------------
# Context processor: luôn gửi cart_count tới tất cả template
# --------------------------
@app.context_processor
def inject_cart_count():
    count = 0
    if session.get("user_id"):
        count = cart_collection.count_documents({"user_id": ObjectId(session["user_id"])})
    return dict(cart_count=count)

# --------------------------
# Đăng ký blueprint
# --------------------------
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(shop_bp, url_prefix="/shop")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(main_bp)

if __name__ == "__main__":
    app.run(debug=True)
