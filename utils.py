from flask import jsonify, current_app

def api_response(data=None, message=None, success=True, status_code=200):
    """Standard API response format"""
    response = {
        'success': success,
        'message': message,
        'data': data
    }
    return jsonify(response), status_code


def get_plan_limits(plan):
    """Get limits for a specific plan"""
    return current_app.config.get('PLANS', {}).get(plan, current_app.config['PLANS']['free'])
