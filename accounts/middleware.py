from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

class NoCacheMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Only add no-cache headers to JS files, not CSS, to avoid loading issues
        if request.path.startswith('/static/') and request.path.endswith('.js'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response

class VerificationMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                # Admin and superusers bypass verification check
                if profile.role == 'admin' or request.user.is_superuser:
                    return None
                
                if not profile.is_verified:
                    # Allow access to pending verification, logout, profile view, and static/media files
                    allowed_url_names = [
                        'accounts:pending_verification', 
                        'accounts:logout', 
                        'accounts:profile', 
                        'accounts:edit_profile'
                    ]
                    
                    try:
                        current_url_name = f"{request.resolver_match.namespace}:{request.resolver_match.url_name}" if request.resolver_match.namespace else request.resolver_match.url_name
                    except Exception:
                        current_url_name = None
                        
                    if current_url_name in allowed_url_names or request.path.startswith('/static/') or request.path.startswith('/media/'):
                        return None
                        
                    return redirect(reverse('accounts:pending_verification'))
            except Exception:
                try:
                    current_url_name = f"{request.resolver_match.namespace}:{request.resolver_match.url_name}" if request.resolver_match.namespace else request.resolver_match.url_name
                except Exception:
                    current_url_name = None
                    
                if current_url_name in ['accounts:create_profile', 'accounts:logout']:
                    return None
                return redirect(reverse('accounts:create_profile'))
        return None

