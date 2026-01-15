from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = "supersecretkey"

    from app.routes.shop import shop_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(shop_bp, url_prefix="/shop")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.route("/")
    def home():
        from flask import render_template
        return render_template("home.html")

    return app
