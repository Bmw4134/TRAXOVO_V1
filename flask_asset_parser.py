# flask_asset_parser.py

def parse_asset_meta(asset_id):
    if not asset_id:
        return {"driverName": "", "rawId": ""}

    import re
    match_parentheses = re.search(r"\((.*?)\)", asset_id)
    match_dash = asset_id.split(" - ")

    if len(match_dash) > 1:
        driver_name = match_dash[1].strip()
    elif match_parentheses:
        driver_name = match_parentheses.group(1).strip()
    else:
        driver_name = asset_id.strip()

    raw_id = re.sub(r"[^0-9]", "", match_dash[0]).strip()
    return {"driverName": driver_name, "rawId": raw_id}


def inject_asset_meta_context(user_input, context=None):
    if context is None:
        context = []
    meta = parse_asset_meta(user_input)
    if meta["driverName"] and meta["rawId"]:
        context.append(f"Asset {meta['rawId']} is assigned to {meta['driverName']}")
    return context


# === Example Flask Usage ===
# from flask import Flask, request, jsonify
# from flask_asset_parser import inject_asset_meta_context
# app = Flask(__name__)
#
# @app.route('/parse', methods=['POST'])
# def parse():
#     data = request.json
#     context = inject_asset_meta_context(data.get('asset_id'))
#     return jsonify({"context": context})