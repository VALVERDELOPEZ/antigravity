"""
Lead Finder AI - Email Deliverability Validator
=================================================
Validates email addresses for deliverability without sending actual emails.

Validation Levels:
1. Syntax validation (regex)
2. Domain validation (MX record check)
3. Disposable email detection
4. Role-based email detection (info@, support@, etc.)

Strategy: $0 cost validation using DNS lookups and pattern matching.
For production at scale, consider integrating with ZeroBounce, Hunter.io, etc.
"""
import re
import dns.resolver
import socket
import logging
from dataclasses import dataclass
from typing import Optional, Tuple
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Common disposable email domains (top 100)
DISPOSABLE_DOMAINS = {
    '10minutemail.com', 'tempmail.com', 'throwaway.email', 'guerrillamail.com',
    'mailinator.com', 'temp-mail.org', 'fakeinbox.com', 'dispostable.com',
    'getnada.com', 'maildrop.cc', 'yopmail.com', 'tempail.com', 'trashmail.com',
    'mohmal.com', 'tempmailaddress.com', 'temp-mail.io', 'emailondeck.com',
    'minutemail.com', 'spamgourmet.com', 'mytrashmail.com', 'sharklasers.com',
    'guerrillamail.info', 'grr.la', 'mailnesia.com', 'mailcatch.com',
    'spamavert.com', 'spamfree24.org', 'bugmenot.com', 'mailinater.com',
    'spam4.me', 'trashmail.net', 'bouncr.com', 'clrmail.com', 'dropmail.me',
    'emailondeck.com', 'fakemailgenerator.com', 'getairmail.com', 'jetable.org',
    'mailnesia.com', 'mintemail.com', 'spamex.com', 'tempr.email', 'throwam.com',
}

# Role-based email prefixes (often not personal)
ROLE_BASED_PREFIXES = {
    'info', 'support', 'admin', 'sales', 'contact', 'hello', 'help',
    'billing', 'noreply', 'no-reply', 'webmaster', 'postmaster', 'hostmaster',
    'marketing', 'press', 'media', 'hr', 'jobs', 'careers', 'team',
    'office', 'feedback', 'abuse', 'security', 'legal', 'privacy',
}


@dataclass
class EmailValidationResult:
    """Result of email validation"""
    email: str
    is_valid: bool
    is_deliverable: bool  # Can we actually send to this email?
    is_disposable: bool
    is_role_based: bool
    has_mx_record: bool
    score: int  # 0-100 deliverability score
    reason: str
    domain: str = ""
    
    def to_dict(self):
        return {
            'email': self.email,
            'is_valid': self.is_valid,
            'is_deliverable': self.is_deliverable,
            'is_disposable': self.is_disposable,
            'is_role_based': self.is_role_based,
            'has_mx_record': self.has_mx_record,
            'score': self.score,
            'reason': self.reason,
            'domain': self.domain,
        }


class EmailValidator:
    """
    Validate email addresses for deliverability.
    Uses DNS lookups and pattern matching for $0 cost validation.
    """
    
    # RFC 5322 compliant email regex
    EMAIL_REGEX = re.compile(
        r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}"
        r"[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )
    
    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        # Configure DNS resolver
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout
    
    def validate_syntax(self, email: str) -> bool:
        """Check if email has valid syntax"""
        if not email or len(email) > 254:
            return False
        return bool(self.EMAIL_REGEX.match(email))
    
    def extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        try:
            return email.split('@')[1].lower()
        except (IndexError, AttributeError):
            return None
    
    def is_disposable(self, domain: str) -> bool:
        """Check if email domain is a disposable email provider"""
        return domain.lower() in DISPOSABLE_DOMAINS
    
    def is_role_based(self, email: str) -> bool:
        """Check if email is role-based (not personal)"""
        try:
            local_part = email.split('@')[0].lower()
            return local_part in ROLE_BASED_PREFIXES
        except Exception:
            return False
    
    @lru_cache(maxsize=1000)
    def check_mx_record(self, domain: str) -> Tuple[bool, str]:
        """
        Check if domain has valid MX records.
        Uses caching to avoid repeated lookups.
        """
        try:
            # Try to get MX records
            mx_records = self.resolver.resolve(domain, 'MX')
            if mx_records:
                return True, f"MX: {str(mx_records[0].exchange)}"
        except dns.resolver.NXDOMAIN:
            return False, "Domain does not exist"
        except dns.resolver.NoAnswer:
            # No MX record, try A record fallback
            try:
                a_records = self.resolver.resolve(domain, 'A')
                if a_records:
                    return True, "A record fallback (no MX)"
            except Exception:
                pass
            return False, "No MX or A record"
        except dns.resolver.Timeout:
            return False, "DNS timeout"
        except Exception as e:
            return False, f"DNS error: {str(e)[:50]}"
        
        return False, "Unknown error"
    
    def calculate_score(self, 
                       syntax_valid: bool,
                       has_mx: bool,
                       is_disposable: bool,
                       is_role_based: bool) -> int:
        """
        Calculate deliverability score (0-100).
        Higher = better deliverability.
        """
        score = 0
        
        if not syntax_valid:
            return 0
        
        score += 30  # Base score for valid syntax
        
        if has_mx:
            score += 40  # Major boost for valid MX
        
        if not is_disposable:
            score += 20  # Not disposable
        
        if not is_role_based:
            score += 10  # Personal email preferred
        
        return min(100, score)
    
    def validate(self, email: str) -> EmailValidationResult:
        """
        Comprehensive email validation.
        
        Returns EmailValidationResult with:
        - is_valid: Email syntax is correct
        - is_deliverable: Email is likely deliverable
        - score: 0-100 deliverability score
        """
        email = email.strip().lower() if email else ""
        
        # Step 1: Syntax validation
        if not self.validate_syntax(email):
            return EmailValidationResult(
                email=email,
                is_valid=False,
                is_deliverable=False,
                is_disposable=False,
                is_role_based=False,
                has_mx_record=False,
                score=0,
                reason="Invalid email syntax"
            )
        
        # Step 2: Extract domain
        domain = self.extract_domain(email)
        if not domain:
            return EmailValidationResult(
                email=email,
                is_valid=False,
                is_deliverable=False,
                is_disposable=False,
                is_role_based=False,
                has_mx_record=False,
                score=0,
                reason="Could not extract domain"
            )
        
        # Step 3: Check disposable
        is_disposable = self.is_disposable(domain)
        
        # Step 4: Check role-based
        is_role_based = self.is_role_based(email)
        
        # Step 5: Check MX records
        has_mx, mx_reason = self.check_mx_record(domain)
        
        # Step 6: Calculate score
        score = self.calculate_score(
            syntax_valid=True,
            has_mx=has_mx,
            is_disposable=is_disposable,
            is_role_based=is_role_based
        )
        
        # Determine deliverability
        is_deliverable = has_mx and not is_disposable and score >= 50
        
        # Build reason
        reasons = []
        if is_disposable:
            reasons.append("Disposable email")
        if is_role_based:
            reasons.append("Role-based address")
        if not has_mx:
            reasons.append(mx_reason)
        
        if not reasons:
            reason = "Valid and deliverable"
        else:
            reason = "; ".join(reasons)
        
        return EmailValidationResult(
            email=email,
            is_valid=True,
            is_deliverable=is_deliverable,
            is_disposable=is_disposable,
            is_role_based=is_role_based,
            has_mx_record=has_mx,
            score=score,
            reason=reason,
            domain=domain
        )
    
    def validate_batch(self, emails: list) -> list:
        """Validate multiple emails"""
        return [self.validate(email) for email in emails]


# Singleton instance
_validator = None

def get_validator() -> EmailValidator:
    """Get or create validator singleton"""
    global _validator
    if _validator is None:
        _validator = EmailValidator()
    return _validator


def validate_email(email: str) -> EmailValidationResult:
    """Convenience function for single email validation"""
    return get_validator().validate(email)


def validate_emails(emails: list) -> list:
    """Convenience function for batch validation"""
    return get_validator().validate_batch(emails)


if __name__ == "__main__":
    # Test validation
    test_emails = [
        "john@gmail.com",
        "test@mailinator.com",  # Disposable
        "info@company.com",  # Role-based
        "invalid-email",
        "user@nonexistentdomain12345.com",
    ]
    
    validator = EmailValidator()
    
    print("\n" + "=" * 60)
    print("EMAIL VALIDATION TEST")
    print("=" * 60)
    
    for email in test_emails:
        result = validator.validate(email)
        print(f"\n📧 {email}")
        print(f"   Valid: {result.is_valid} | Deliverable: {result.is_deliverable}")
        print(f"   Score: {result.score}/100 | Reason: {result.reason}")
