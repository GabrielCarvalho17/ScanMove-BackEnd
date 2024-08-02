from django.conf import settings
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import RefreshToken

class LoginRequiredMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verifica se a solicitação aceita 'text/html' (indicando Browsable API)
        is_browsable_api = 'text/html' in request.headers.get('Accept', '')

        # Evita redirecionamento se já estiver na página de login
        is_login_url = request.path == settings.LOGIN_URL

        # Redireciona para a página de login se o usuário não estiver autenticado e não estiver já na página de login
        if is_browsable_api and not request.user.is_authenticated and not is_login_url:
            return redirect(f'{settings.LOGIN_URL}?next={request.path}')

        # Adiciona o token JWT ao header da requisição para o Browsable API
        if is_browsable_api and request.user.is_authenticated:
            if 'access_token' not in request.session:
                # Obter o token de acesso JWT
                refresh = RefreshToken.for_user(request.user)
                access_token = str(refresh.access_token)
                
                # Armazenar o token na sessão
                request.session['access_token'] = access_token

            # Adicionar o token de acesso aos headers da requisição
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {request.session["access_token"]}'

        response = self.get_response(request)
        return response
