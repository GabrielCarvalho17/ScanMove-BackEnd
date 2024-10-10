from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

def manipulador_de_exceções_jwt_personalizado(exc, context):
    """
    Manipulador de exceção customizado para formatar a resposta de erros JWT no padrão desejado.
    """
    # Obtém a resposta padrão gerada pelo DRF
    resposta = exception_handler(exc, context)

    if isinstance(exc, (InvalidToken, TokenError)) and resposta is not None:
        # Extrai as informações detalhadas para criar o novo formato
        messages = exc.detail.get("messages", [])
        token_info = messages[0] if len(messages) > 0 else {}

        # Define o novo formato para a resposta
        resposta.data = {
            "codigo": exc.detail.get("code", "token_error"),
            "classe": token_info.get("token_class", "Unknown"),
            "tipo": token_info.get("token_type", "Unknown"),
            "mensagem": token_info.get("message", "O token é inválido ou expirado"),
            "detalhes": exc.detail.get("detail", "Erro desconhecido com o token"),
        }

    return resposta