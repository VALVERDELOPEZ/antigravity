from flask import render_template, jsonify
from . import public_bp

@public_bp.route('/')
def landing():
    """Landing page"""
    return render_template('landing.html')


@public_bp.route('/pricing')
def pricing():
    """Pricing page"""
    return render_template('pricing.html')


@public_bp.route('/health')
def health_check():
    """Health check endpoint for deployment probes (Render, Kubernetes, etc.)"""
    return jsonify({"status": "healthy", "service": "lead-finder-ai"}), 200
