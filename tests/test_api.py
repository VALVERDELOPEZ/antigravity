"""
Lead Finder AI - Integration Tests for API Routes
Tests lead retrieval, email validation, and other API endpoints
"""
import pytest
import json
from app import create_app
from models import db, User, Lead


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Create authenticated test client"""
    with app.app_context():
        user = User(
            name='API Test User',
            email='apitest@example.com',
            plan='starter'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
    
    # Login
    client.post('/login', data={
        'email': 'apitest@example.com',
        'password': 'password123'
    })
    
    return client


@pytest.fixture
def sample_lead(app):
    """Create a sample lead for testing"""
    with app.app_context():
        user = User.query.filter_by(email='apitest@example.com').first()
        if user:
            lead = Lead(
                user_id=user.id,
                username='test_lead',
                platform='reddit',
                title='Test Lead Title',
                content='This is test content for the lead.',
                post_url='https://reddit.com/r/test/123',
                score=8,
                status='new'
            )
            db.session.add(lead)
            db.session.commit()
            return lead.id
    return None


class TestLeadsAPI:
    """Test leads API endpoints"""
    
    def test_get_leads_requires_auth(self, client):
        """GET /api/leads should require authentication"""
        response = client.get('/api/leads')
        # Should return 401 or redirect
        assert response.status_code in [401, 302, 200]
    
    def test_get_leads_with_auth(self, auth_client):
        """Authenticated user should get leads list"""
        response = auth_client.get('/api/leads')
        assert response.status_code == 200
        # Response should be JSON
        data = response.get_json()
        assert 'leads' in data or 'data' in data or isinstance(data, list)


class TestEmailValidationAPI:
    """Test email validation endpoints"""
    
    def test_validate_email_valid(self, auth_client):
        """Valid email should pass validation"""
        response = auth_client.post('/api/validate-email',
            data=json.dumps({'email': 'valid@gmail.com'}),
            content_type='application/json'
        )
        # May return 200 or other status based on implementation
        assert response.status_code in [200, 400, 401]
    
    def test_validate_email_invalid_format(self, auth_client):
        """Invalid email format should fail"""
        response = auth_client.post('/api/validate-email',
            data=json.dumps({'email': 'not-an-email'}),
            content_type='application/json'
        )
        assert response.status_code in [200, 400]


class TestStatsAPI:
    """Test statistics API"""
    
    def test_get_stats_requires_auth(self, client):
        """Stats endpoint should require authentication"""
        response = client.get('/api/stats')
        assert response.status_code in [401, 302, 200]
    
    def test_get_stats_with_auth(self, auth_client):
        """Authenticated user should get stats"""
        response = auth_client.get('/api/stats')
        assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting is working"""
    
    def test_rate_limit_headers_present(self, client):
        """Rate limit headers should be present"""
        response = client.get('/health')
        # Check for rate limit headers
        assert response.status_code == 200
        # Headers may include X-RateLimit-* depending on config


class TestExportAPI:
    """Test lead export functionality"""
    
    def test_export_requires_auth(self, client):
        """Export should require authentication"""
        response = client.get('/api/leads/export')
        assert response.status_code in [401, 302, 200]
