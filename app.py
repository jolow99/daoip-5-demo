from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

def get_data_dir():
    """Get the absolute path to the data directory."""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_dir, 'daoip-5', 'json', 'stellar')

def load_stellar_data():
    """Load Stellar Community Fund data."""
    try:
        stellar_path = os.path.join(get_data_dir(), 'grants_pool.json')
        with open(stellar_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        app.logger.error(f"Error loading stellar data: {str(e)}")
        return {"grantPools": []}

def load_grant_pool_applications(pool_id):
    """Load applications for a specific grant pool."""
    try:
        applications_path = os.path.join(get_data_dir(), f'scf-{pool_id}_applications_uri.json')
        with open(applications_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        app.logger.warning(f"Applications file not found for pool {pool_id}")
        return {"applications": []}
    except Exception as e:
        app.logger.error(f"Error loading applications for pool {pool_id}: {str(e)}")
        return {"applications": []}

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/api/stellar/overview')
def get_stellar_overview():
    """Get overview statistics for Stellar Community Fund."""
    data = load_stellar_data()
    pools = data['grantPools']
    
    # Calculate statistics, ignoring pools with NaN or invalid data
    total_pools = len(pools)
    total_funding = 0
    total_applications = 0
    total_awards = 0
    
    for pool in pools:
        # Handle funding amount
        try:
            amount = pool['totalGrantPoolSize'][0]['amount']
            if amount != 'NaN':
                total_funding += float(amount)
        except (KeyError, ValueError, IndexError):
            continue
            
        # Handle applications and awards from description
        try:
            if 'received ' in pool['description']:
                apps = int(pool['description'].split('received ')[1].split(' total')[0])
                awards = int(pool['description'].split('and ')[1].split(' were')[0])
                total_applications += apps
                total_awards += awards
        except (ValueError, IndexError):
            continue
    
    return jsonify({
        'name': data['name'],
        'totalPools': total_pools,
        'totalFunding': total_funding,
        'totalApplications': total_applications,
        'totalAwards': total_awards,
        'averagePoolSize': total_funding / total_pools if total_pools > 0 else 0,
        'successRate': (total_awards / total_applications * 100) if total_applications > 0 else 0
    })

@app.route('/api/stellar/pools')
def get_stellar_pools():
    """Get all Stellar grant pools."""
    data = load_stellar_data()
    return jsonify(data['grantPools'])

@app.route('/api/stellar/pools/<int:pool_id>')
def get_stellar_pool(pool_id):
    """Get detailed information about a specific grant pool."""
    data = load_stellar_data()
    pool = next((p for p in data['grantPools'] if p['id'] == pool_id), None)
    
    if pool:
        # Load applications for this pool
        applications = load_grant_pool_applications(pool_id)
        pool['applications'] = applications.get('applications', [])
        
        # Extract metrics from description
        if 'received ' in pool['description']:
            pool['totalApplications'] = int(pool['description'].split('received ')[1].split(' total')[0])
            pool['totalAwards'] = int(pool['description'].split('and ')[1].split(' were')[0])
        
        return jsonify(pool)
    
    return jsonify({'error': 'Grant pool not found'}), 404

@app.route('/debug/paths')
def debug_paths():
    """Debug endpoint to check paths and file existence."""
    data_dir = get_data_dir()
    stellar_path = os.path.join(data_dir, 'grants_pool.json')
    
    return jsonify({
        'base_dir': os.path.abspath(os.path.dirname(__file__)),
        'data_dir': data_dir,
        'stellar_path': stellar_path,
        'stellar_exists': os.path.exists(stellar_path),
        'data_dir_exists': os.path.exists(data_dir),
        'data_dir_contents': os.listdir(data_dir) if os.path.exists(data_dir) else []
    })

if __name__ == '__main__':
    app.run(debug=True) 