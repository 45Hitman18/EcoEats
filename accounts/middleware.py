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
                if not request.user.profile.is_verified:
                    messages.error(request, 'Your account has been blocked. Please contact support.')
                    logout(request)
                    return redirect(reverse('accounts:login'))
            except:
                messages.error(request, 'Your account has been blocked. Please contact support.')
                logout(request)
                return redirect(reverse('accounts:login'))
        return None
