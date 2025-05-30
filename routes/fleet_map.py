@app.route('/fleet_map')
def fleet_map_view():
    gps_data = get_gps_data()
    job_sites = get_job_sites()

    return render_template('fleet_map.html', gps_data=gps_data, job_sites=job_sites)

def get_gps_data():
    # Function to get GPS data of assets
    return []

def get_job_sites():
    # Function to get job site data
    return []