from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from .serializers import UsuarioSerializer
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import AutenticacaoSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework_simplejwt.exceptions import TokenError


@extend_schema(
    tags=["Usuários"],
)
class UsuarioView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    authentication_classes = [JWTAuthentication]


@extend_schema(
    tags=["Autenticação"],
    operation_id="obter_token",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password": {"type": "string"},
            },
            "required": ["username", "password"],
        }
    },
    description="Endpoint para obtenção de tokens JWT.",
    responses={
        200: AutenticacaoSerializer,
        400: OpenApiResponse(
            description="Requisição inválida. Verifique os campos fornecidos."
        ),
        401: OpenApiResponse(description="Usuário ou senha incorretos"),
    },
)
class ObterTokenView(TokenObtainPairView):
    serializer_class = AutenticacaoSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"mensagem": "Requisição inválida. Verifique os campos fornecidos."},
                status=400,
            )

        user = authenticate(request, username=username, password=password)
        if user is not None:
            refresh_token = RefreshToken.for_user(user)
            access_token = refresh_token.access_token

            refresh_token["username"] = username
            access_token["username"] = username

            return Response(
                {
                    "username": username,
                    "refresh": str(refresh_token),
                    "access": str(access_token),
                },
                status=200,
            )
        else:
            return Response({"mensagem": "Usuário ou senha incorretos"}, status=401)


@extend_schema(
    tags=["Autenticação"],
    operation_id="renovar_token",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "refresh": {"type": "string"},
            },
            "required": ["refresh"],
        }
    },
    description="Endpoint para renovação de tokens JWT.",
    responses={
        200: AutenticacaoSerializer,
        400: OpenApiResponse(
            description="Requisição inválida. O campo `refresh` é obrigatório."
        ),
        401: OpenApiResponse(description="Token de atualização inválido ou expirado."),
    },
)
class AtualizarTokenView(TokenRefreshView):
    serializer_class = AutenticacaoSerializer

    def post(self, request, *args, **kwargs):
        refresh_token_str = request.data.get("refresh")

        if not refresh_token_str:
            return Response(
                {"mensagem": "Requisição inválida. O campo `refresh` é obrigatório."},
                status=400,
            )

        try:
            refresh_token = RefreshToken(refresh_token_str)
            username = refresh_token.get("username")

            # Obtenha o usuário a partir do nome de usuário (username)
            user = User.objects.get(username=username)

            # Gere novos tokens usando o usuário obtido
            novo_refresh = RefreshToken.for_user(user)
            novo_access = novo_refresh.access_token

            novo_refresh["username"] = username
            novo_access["username"] = username

            return Response(
                {
                    "username": username,
                    "refresh": str(novo_refresh),
                    "access": str(novo_access),
                },
                status=200,
            )

        except User.DoesNotExist:
            return Response({"mensagem": "Usuário não encontrado."}, status=404)
        except TokenError:
            return Response(
                {"mensagem": "Token de atualização inválido ou expirado."}, status=401
            )



