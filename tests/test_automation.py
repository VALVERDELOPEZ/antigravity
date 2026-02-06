import unittest
from datetime import datetime, timedelta
from flask import Flask
from models import db, Lead, User
from automation.follow_up_engine import FollowUpEngine
from app import create_app

class TestAutomation(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Override config for testing
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['TESTING'] = True
        
        db.create_all()
        
        # Create test user
        self.user = User(email='test@example.com', name='Test User')
        self.user.set_password('password')
        db.session.add(self.user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def test_should_continue_sequence(self):
        """Test sequence continuation logic"""
        # Create a lead
        lead = Lead(
            user_id=self.user.id,
            email='lead@example.com',
            status='new',
            title='Test Lead'
        )
        db.session.add(lead)
        db.session.commit()
        
        engine = FollowUpEngine()
        
        # 1. Normal case
        should, reason = engine.should_continue_sequence(lead.id)
        self.assertTrue(should)
        
        # 2. Replied
        lead.email_replied = True
        db.session.commit()
        should, reason = engine.should_continue_sequence(lead.id)
        self.assertFalse(should)
        self.assertEqual(reason, "Lead replied")
        
        # 3. Converted
        lead.email_replied = False
        lead.status = 'converted'
        db.session.commit()
        should, reason = engine.should_continue_sequence(lead.id)
        self.assertFalse(should)
        
    def test_app_structure(self):
        """Verify blueprints are registered"""
        self.assertIn('dashboard', self.app.blueprints)
        self.assertIn('auth', self.app.blueprints)
        self.assertIn('api', self.app.blueprints)

if __name__ == '__main__':
    unittest.main()
