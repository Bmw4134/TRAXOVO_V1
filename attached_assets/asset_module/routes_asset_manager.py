from flask import Blueprint, render_template
asset_manager = Blueprint('asset_manager', __name__)

@asset_manager.route("/asset-manager")
def asset_dashboard():
    return render_template("asset_manager.html")
