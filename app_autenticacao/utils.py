from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.response import Response

def manipulador_de_exceções_jwt_personalizado(exc, context):
    """
    Manipulador de exceção customizado para formatar a resposta de erros JWT no padrão desejado.
    """
    # Obtém a resposta padrão gerada pelo DRF
    resposta = exception_handler(exc, context)

    # Verifica se a exceção é uma das exceções relacionadas a JWT
    if isinstance(exc, (InvalidToken, TokenError)) and resposta is not None:
        detail = getattr(exc, "detail", {})  # Garante que `exc.detail` exista
        messages = detail.get("messages", [])
        token_info = messages[0] if len(messages) > 0 else {}

        # Define valores padrão para a classe e tipo de token
        token_class = token_info.get("token_class", "Unknown")
        token_type = token_info.get("token_type", "Unknown")

        # Identifica o tipo de token pelo caminho da requisição
        if "refresh" in context.get("request").path:
            token_class = "RefreshToken"
            token_type = "refresh"

        # Define o novo formato para a resposta
        resposta.data = {
            "codigo": detail.get("code", "token_error"),
            "classe": token_class,
            "tipo": token_type,
            "mensagem": token_info.get("message", "O token é inválido ou expirado"),
            "detalhes": detail.get("detail", "Erro desconhecido com o token"),
        }

    # **Ponto principal**: Padroniza `detail` para `mensagem` em todas as respostas de erro
    if resposta is not None and 'detail' in resposta.data:
        resposta.data['mensagem'] = resposta.data.pop('detail')  # Substitui `detail` por `mensagem`

    return resposta
