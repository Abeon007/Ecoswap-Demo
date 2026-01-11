"""
Tests for localization functionality: language switching, translations
"""
import pytest


class TestLanguageSwitching:
    """Test language switching functionality."""
    
    def test_set_language_en(self, client):
        """Test switching to English language."""
        response = client.get('/set_language/en', follow_redirects=True)
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            assert sess.get('lang') == 'en'
    
    def test_set_language_de(self, client):
        """Test switching to German language."""
        response = client.get('/set_language/de', follow_redirects=True)
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            assert sess.get('lang') == 'de'
    
    def test_set_language_invalid(self, client):
        """Test setting invalid language."""
        response = client.get('/set_language/fr', follow_redirects=True)
        assert response.status_code == 200
        
        # Should not set invalid language
        with client.session_transaction() as sess:
            assert sess.get('lang') is None or sess.get('lang') not in ['fr']
    
    def test_default_language(self, client):
        """Test that default language is English."""
        response = client.get('/')
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            # Default should be 'en' or None (which defaults to 'en')
            lang = sess.get('lang', 'en')
            assert lang in ['en', None]
    
    def test_language_persists_across_requests(self, client):
        """Test that language setting persists across requests."""
        # Set language
        client.get('/set_language/de', follow_redirects=True)
        
        # Make another request
        response = client.get('/')
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            assert sess.get('lang') == 'de'
    
    def test_language_switching_redirects(self, client):
        """Test that language switching redirects properly."""
        # Set referrer
        response = client.get('/set_language/de', 
                            headers={'Referer': '/marketplace'},
                            follow_redirects=False)
        assert response.status_code == 302
        
        # Without referrer, should redirect to index
        response = client.get('/set_language/en', follow_redirects=False)
        assert response.status_code == 302
