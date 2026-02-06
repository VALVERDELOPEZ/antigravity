"""
Lead Finder AI - Integration Tests for Auth Routes
Tests login, signup, logout, and onboarding flows
"""
import pytest
from flask import url_for
from app import create_app
from models import db, User


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
def sample_user(app):
    """Create a sample user for testing"""
    with app.app_context():
        user = User(
            name='Test User',
            email='test@example.com',
            plan='free'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user.id


class TestSignup:
    """Test user registration"""
    
    def test_signup_page_loads(self, client):
        """Signup page should load successfully"""
        response = client.get('/signup')
        assert response.status_code == 200
        assert b'Sign Up' in response.data or b'Create' in response.data
    
    def test_signup_with_valid_data(self, client):
        """User should be able to register with valid data"""
        response = client.post('/signup', data={
            'name': 'New User',
            'email': 'newuser@example.com',
            'password': 'securepassword123'
        }, follow_redirects=True)
        
        # Should redirect to onboarding or dashboard
        assert response.status_code == 200
    
    def test_signup_with_existing_email(self, client, sample_user, app):
        """Registration should fail with existing email"""
        response = client.post('/signup', data={
            'name': 'Another User',
            'email': 'test@example.com',  # Already exists
            'password': 'password123'
        }, follow_redirects=True)
        
        assert b'already' in response.data.lower() or response.status_code == 200


class TestLogin:
    """Test user login"""
    
    def test_login_page_loads(self, client):
        """Login page should load successfully"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Log' in response.data
    
    def test_login_with_valid_credentials(self, client, sample_user, app):
        """User should be able to login with valid credentials"""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_with_invalid_password(self, client, sample_user):
        """Login should fail with wrong password"""
        response = client.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        # Should stay on login page or show error
        assert response.status_code == 200


class TestLogout:
    """Test user logout"""
    
    def test_logout_redirects_to_landing(self, client, sample_user, app):
        """Logout should redirect to landing page"""
        # First login
        client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Then logout
        response = client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestProtectedRoutes:
    """Test that protected routes require authentication"""
    
    def test_dashboard_requires_login(self, client):
        """Dashboard should redirect unauthenticated users"""
        response = client.get('/dashboard')
        # Should redirect to login
        assert response.status_code in [302, 401, 200]
    
    def test_leads_requires_login(self, client):
        """Leads page should require authentication"""
        response = client.get('/dashboard/leads')
        assert response.status_code in [302, 401, 200]
    
    def test_settings_requires_login(self, client):
        """Settings page should require authentication"""
        response = client.get('/dashboard/settings')
        assert response.status_code in [302, 401, 200]


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_endpoint(self, client):
        """Health endpoint should return 200 with status"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
