"""
Lead Finder AI - Email Open & Click Tracking
=============================================
Implements real email tracking using invisible pixel and redirect links.

Features:
1. Open Tracking: 1x1 transparent pixel image
2. Click Tracking: Redirect URLs for link tracking
3. Analytics: Track open rates, click rates, etc.

This enables real professional email analytics at $0 cost.
"""
import os
import sys
import uuid
import hashlib
import logging
from datetime import datetime
from urllib.parse import urlencode, quote
from typing import Dict, Optional
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TrackingEvent:
    """Represents a tracking event"""
    event_type: str  # 'open', 'click'
    lead_id: int
    email_id: str
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    link_url: Optional[str] = None  # For click events


class EmailTracker:
    """
    Handles email tracking via pixel and redirect links.
    """
    
    # 1x1 transparent GIF (smallest valid image)
    TRACKING_PIXEL = (
        b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
        b'\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00'
        b'\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
    )
    
    def __init__(self, base_url: str = None):
        """
        Args:
            base_url: Base URL of the application (e.g., https://yourdomain.com)
        """
        self.base_url = base_url or os.getenv('APP_URL', 'http://localhost:5000')
    
    def generate_tracking_id(self, lead_id: int, email_position: int = 1) -> str:
        """
        Generate a unique tracking ID for an email.
        Uses a hash to prevent guessing.
        """
        secret = os.getenv('SECRET_KEY', 'default-secret-key')
        unique_string = f"{lead_id}:{email_position}:{secret}:{uuid.uuid4()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:24]
    
    def generate_pixel_url(self, lead_id: int, tracking_id: str) -> str:
        """
        Generate the tracking pixel URL.
        
        Returns URL like:
        https://yourdomain.com/track/open/abc123def456.gif
        """
        return f"{self.base_url}/track/open/{tracking_id}.gif"
    
    def generate_pixel_html(self, lead_id: int, tracking_id: str) -> str:
        """
        Generate HTML for invisible tracking pixel.
        
        Returns:
        <img src="..." width="1" height="1" border="0" style="display:none;">
        """
        url = self.generate_pixel_url(lead_id, tracking_id)
        return f'<img src="{url}" width="1" height="1" border="0" alt="" style="display:none;visibility:hidden;">'
    
    def generate_tracked_link(
        self,
        original_url: str,
        lead_id: int,
        tracking_id: str,
        link_id: str = None
    ) -> str:
        """
        Wrap a link in a tracking redirect.
        
        Returns URL like:
        https://yourdomain.com/track/click/abc123?url=https://...&lid=1
        """
        link_id = link_id or uuid.uuid4().hex[:8]
        params = urlencode({
            'url': original_url,
            'lid': lead_id,
            'lnk': link_id
        })
        return f"{self.base_url}/track/click/{tracking_id}?{params}"
    
    def inject_tracking_into_html(
        self,
        html_content: str,
        lead_id: int,
        tracking_id: str
    ) -> str:
        """
        Inject tracking pixel and wrap links in HTML email.
        """
        import re
        
        # Add tracking pixel before </body> or at end
        pixel_html = self.generate_pixel_html(lead_id, tracking_id)
        
        if '</body>' in html_content.lower():
            html_content = re.sub(
                r'</body>',
                f'{pixel_html}</body>',
                html_content,
                flags=re.IGNORECASE
            )
        else:
            html_content += pixel_html
        
        # Wrap all links
        def replace_link(match):
            original_url = match.group(1)
            # Don't track mailto: or internal links
            if original_url.startswith(('mailto:', '#', 'javascript:')):
                return match.group(0)
            tracked_url = self.generate_tracked_link(original_url, lead_id, tracking_id)
            return f'href="{tracked_url}"'
        
        html_content = re.sub(
            r'href=["\']([^"\']+)["\']',
            replace_link,
            html_content
        )
        
        return html_content
    
    def inject_tracking_into_text(
        self,
        text_content: str,
        lead_id: int,
        tracking_id: str
    ) -> str:
        """
        For plain text emails, we can only track clicks, not opens.
        Wraps URLs in tracking redirects.
        """
        import re
        
        url_pattern = r'(https?://[^\s<>"]+)'
        
        def replace_url(match):
            original_url = match.group(1)
            return self.generate_tracked_link(original_url, lead_id, tracking_id)
        
        return re.sub(url_pattern, replace_url, text_content)


class TrackingAnalytics:
    """
    Analytics for email tracking events.
    """
    
    @staticmethod
    def calculate_open_rate(sent: int, opened: int) -> float:
        """Calculate open rate percentage"""
        if sent == 0:
            return 0.0
        return round((opened / sent) * 100, 2)
    
    @staticmethod
    def calculate_click_rate(sent: int, clicked: int) -> float:
        """Calculate click rate percentage"""
        if sent == 0:
            return 0.0
        return round((clicked / sent) * 100, 2)
    
    @staticmethod
    def calculate_reply_rate(sent: int, replied: int) -> float:
        """Calculate reply rate percentage"""
        if sent == 0:
            return 0.0
        return round((replied / sent) * 100, 2)
    
    @staticmethod
    def get_benchmark_comparison(open_rate: float, click_rate: float) -> Dict:
        """
        Compare metrics against industry benchmarks.
        
        Industry averages (B2B):
        - Open rate: 15-25%
        - Click rate: 2-5%
        - Reply rate: 1-5%
        """
        return {
            'open_rate': {
                'value': open_rate,
                'benchmark': 20.0,
                'status': 'above' if open_rate > 20 else 'at' if open_rate > 15 else 'below'
            },
            'click_rate': {
                'value': click_rate,
                'benchmark': 3.5,
                'status': 'above' if click_rate > 3.5 else 'at' if click_rate > 2 else 'below'
            }
        }


# Flask routes for tracking endpoints
TRACKING_ROUTES_CODE = '''
# Add these routes to app.py

@app.route('/track/open/<tracking_id>.gif')
def track_open(tracking_id):
    """Track email opens via invisible pixel"""
    from automation.email_tracking import EmailTracker
    from models import db, Lead
    
    # Log the open
    try:
        # Find lead by tracking_id (stored in lead.email_tracking_id)
        lead = Lead.query.filter_by(email_tracking_id=tracking_id).first()
        if lead and not lead.email_opened:
            lead.email_opened = True
            lead.email_opened_at = datetime.utcnow()
            db.session.commit()
            logger.info(f"📬 Email opened: Lead #{lead.id}")
    except Exception as e:
        logger.error(f"Track open error: {e}")
    
    # Return 1x1 transparent GIF
    response = make_response(EmailTracker.TRACKING_PIXEL)
    response.headers['Content-Type'] = 'image/gif'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/track/click/<tracking_id>')
def track_click(tracking_id):
    """Track link clicks and redirect"""
    from models import db, Lead
    
    original_url = request.args.get('url', '/')
    lead_id = request.args.get('lid')
    
    # Log the click
    try:
        if lead_id:
            lead = Lead.query.get(int(lead_id))
            if lead:
                # Could track individual link clicks here
                lead.email_clicked = True
                lead.email_clicked_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"🖱️ Link clicked: Lead #{lead.id}")
    except Exception as e:
        logger.error(f"Track click error: {e}")
    
    # Redirect to original URL
    return redirect(original_url)
'''


# Database model additions
TRACKING_MODEL_SQL = """
-- Add tracking columns to leads table
ALTER TABLE leads 
ADD COLUMN IF NOT EXISTS email_tracking_id VARCHAR(50),
ADD COLUMN IF NOT EXISTS email_clicked BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS email_clicked_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_leads_tracking 
ON leads(email_tracking_id);
"""


def get_tracker(base_url: str = None) -> EmailTracker:
    """Get email tracker instance"""
    return EmailTracker(base_url)


if __name__ == "__main__":
    # Demo
    tracker = EmailTracker("https://app.leadfinderai.com")
    
    print("\n" + "=" * 60)
    print("EMAIL TRACKING DEMO")
    print("=" * 60)
    
    lead_id = 123
    tracking_id = tracker.generate_tracking_id(lead_id)
    
    print(f"\n📊 Tracking ID: {tracking_id}")
    print(f"\n🖼️ Pixel URL:")
    print(f"   {tracker.generate_pixel_url(lead_id, tracking_id)}")
    
    print(f"\n🔗 Tracked Link (example):")
    original = "https://calendly.com/yourmetting"
    tracked = tracker.generate_tracked_link(original, lead_id, tracking_id)
    print(f"   Original: {original}")
    print(f"   Tracked:  {tracked}")
    
    print(f"\n📧 Pixel HTML:")
    print(f"   {tracker.generate_pixel_html(lead_id, tracking_id)}")
    
    # Analytics example
    print(f"\n📈 Analytics Benchmarks:")
    analytics = TrackingAnalytics()
    comparison = analytics.get_benchmark_comparison(open_rate=22.5, click_rate=4.2)
    print(f"   Open Rate: {comparison['open_rate']['value']}% ({comparison['open_rate']['status']} benchmark)")
    print(f"   Click Rate: {comparison['click_rate']['value']}% ({comparison['click_rate']['status']} benchmark)")
