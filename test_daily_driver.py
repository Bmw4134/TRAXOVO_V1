from flask import Flask
from routes.daily_driver_authentic import daily_driver_bp

app = Flask(__name__)
app.register_blueprint(daily_driver_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=True)