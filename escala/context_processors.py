# escala/context_processors.py

from django.utils import timezone
from decimal import Decimal
from .models import EscalaUsuario  # Importa o modelo correto


def remuneration_processor(request):
    """
    Adiciona a remuneração confirmada do mês atual ao contexto do template
    para usuários autenticados.
    """
    total_remuneration = None  # Inicializa como None

    if request.user.is_authenticated:
        try:
            current_date = timezone.now().date()
            current_year = current_date.year
            current_month = current_date.month

            total_remuneration = Decimal("0.00")  # Usa Decimal para precisão

            # Busca apenas as escalas CONFIRMADAS do usuário para o mês/ano ATUAL
            escalas_confirmadas_mes_atual = EscalaUsuario.objects.filter(
                usuario=request.user,
                data__year=current_year,
                data__month=current_month,
                confirmado_admin=True,  # Filtra apenas as confirmadas
            )

            # Soma os valores usando a property 'valor_turno' do modelo
            for escala in escalas_confirmadas_mes_atual:
                total_remuneration += escala.valor_turno

        except Exception as e:
            # Em caso de erro (improvável, mas seguro), não quebra a página
            print(f"Erro no context processor remuneration_processor: {e}")
            total_remuneration = Decimal(
                "0.00"
            )  # Ou None, dependendo de como quer tratar erros

    # Retorna o dicionário que será mesclado ao contexto do template
    return {"current_month_remuneration": total_remuneration}
