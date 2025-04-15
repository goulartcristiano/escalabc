# escala/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# --- CORREÇÃO: Importar EscalaUsuario ---
from .models import EscalaUsuario, TurnoEscolha
from .forms import EscalaForm
from .utils import gerar_calendario_mes
from datetime import date
from decimal import Decimal
from django.core.exceptions import ValidationError  # Importar ValidationError


@login_required
def gerenciar_escala(request):
    """
    View para gerenciar (adicionar, editar, visualizar) as escalas do usuário logado.
    Calcula e exibe a remuneração total confirmada para o mês visualizado.
    """
    # --- Determina o Ano e Mês a serem exibidos ---
    try:
        current_year = int(request.GET.get("ano", timezone.now().year))
        current_month = int(request.GET.get("mes", timezone.now().month))
        if not 1 <= current_month <= 12:
            raise ValueError("Mês inválido")
        current_date = date(current_year, current_month, 1)
    except (ValueError, TypeError):
        messages.warning(request, _("Mês ou ano inválido. Exibindo o mês atual."))
        current_date = timezone.now().date().replace(day=1)
        current_year = current_date.year
        current_month = current_date.month
        return redirect(
            reverse("escala:gerenciar_escala")
            + f"?ano={current_year}&mes={current_month}"
        )

    # --- Variáveis para controle de edição e formulário ---
    editing_mode = False
    escala_instance = None
    # default_date_value pega data do GET (botão '+') ou do POST (erro de form)
    default_date_value = request.GET.get(
        "data_selecionada", request.POST.get("data", None)
    )
    form = None  # Inicializa form como None

    # --- Lógica de Edição ---
    edit_pk = request.GET.get("editar")
    if edit_pk:
        # Busca a escala específica do usuário logado
        escala_instance = get_object_or_404(
            EscalaUsuario, pk=edit_pk, usuario=request.user
        )

        # Regra: Não permite editar escalas confirmadas
        if escala_instance.confirmado_admin:
            messages.warning(
                request,
                _("Não é possível editar uma escala já confirmada pelo administrador."),
            )
            return redirect(
                reverse("escala:gerenciar_escala")
                + f"?ano={escala_instance.data.year}&mes={escala_instance.data.month}"
            )

        editing_mode = True
        # Define a data padrão APENAS se não houver um POST (evita sobrescrever erro)
        if not request.POST:
            default_date_value = escala_instance.data.strftime("%Y-%m-%d")
        # edit_turno_value não é mais necessário aqui, o form cuida disso com 'instance'

    # --- Processamento do Formulário (POST) ---
    if request.method == "POST":
        # Passa o usuário para o form para validação e associação
        form = EscalaForm(
            request.POST,
            instance=escala_instance if editing_mode else None,
            user=request.user,
        )
        if form.is_valid():
            try:
                # O form.save() já associa o usuário e trata duplicatas (via clean_data)
                escala_salva = form.save(commit=True)

                if editing_mode:
                    messages.success(
                        request,
                        _("Escala para %(data)s atualizada com sucesso!")
                        % {"data": escala_salva.data.strftime("%d/%m/%Y")},
                    )
                else:
                    messages.success(
                        request,
                        _("Escala para %(data)s adicionada com sucesso!")
                        % {"data": escala_salva.data.strftime("%d/%m/%Y")},
                    )

                # Redireciona para o mês/ano da escala salva
                return redirect(
                    reverse("escala:gerenciar_escala")
                    + f"?ano={escala_salva.data.year}&mes={escala_salva.data.month}"
                )

            except ValidationError as e:  # Captura erros do model.clean ou form.clean
                form.add_error(None, e)  # Adiciona como erro geral do form
                messages.error(
                    request, _("Erro ao salvar a escala: Verifique os avisos.")
                )
            except Exception as e:  # Outros erros inesperados
                messages.error(
                    request, _("Ocorreu um erro inesperado ao salvar a escala.")
                )
                # Considerar logar o erro 'e' para depuração
        else:
            # Form inválido (erros de campo ou validação do form)
            messages.error(request, _("Erro ao salvar a escala. Verifique os campos."))
            # Mantém os valores submetidos para exibir no formulário novamente
            default_date_value = request.POST.get("data", default_date_value)
            # edit_turno_value não é necessário, o form inválido mantém o valor selecionado
            if escala_instance:  # Mantém modo edição se estava editando e falhou
                editing_mode = True

    # --- Criação do Formulário (GET ou POST falhou) ---
    if not form:  # Se o form não foi criado/validado no bloco POST
        initial_data = {}
        # Preenche initial APENAS se não for um POST inválido
        if not request.POST:
            if editing_mode:
                # O form usará a 'instance' para preencher os campos
                pass  # Não precisa de initial se instance é passada
            elif default_date_value:
                initial_data = {"data": default_date_value}

        # Passa o usuário para o form
        # Passa 'instance' se estiver editando
        form = EscalaForm(
            initial=initial_data,
            instance=escala_instance if editing_mode else None,
            user=request.user,
        )

    # --- CÁLCULO DA REMUNERAÇÃO MENSAL CONFIRMADA ---
    total_remuneration = Decimal("0.00")
    escalas_confirmadas_mes = EscalaUsuario.objects.filter(
        usuario=request.user,
        data__year=current_year,
        data__month=current_month,
        confirmado_admin=True,
    )
    for escala in escalas_confirmadas_mes:
        total_remuneration += escala.valor_turno

    # --- Geração do Calendário ---
    escalas_usuario_mes = EscalaUsuario.objects.filter(
        usuario=request.user, data__year=current_year, data__month=current_month
    ).select_related("usuario")
    escalas_dict = {escala.data: escala for escala in escalas_usuario_mes}
    calendar_weeks = gerar_calendario_mes(current_year, current_month, escalas_dict)

    # --- Navegação entre meses ---
    prev_month_date = (
        current_date.replace(day=1) - timezone.timedelta(days=1)
    ).replace(day=1)
    next_month_date = (
        current_date.replace(day=28) + timezone.timedelta(days=4)
    ).replace(day=1)
    previous_month_url = (
        reverse("escala:gerenciar_escala")
        + f"?ano={prev_month_date.year}&mes={prev_month_date.month}"
    )
    next_month_url = (
        reverse("escala:gerenciar_escala")
        + f"?ano={next_month_date.year}&mes={next_month_date.month}"
    )

    # --- Contexto para o Template (Ajustado) ---
    context = {
        "form": form,
        "calendar_weeks": calendar_weeks,
        "current_month": current_month,
        "current_year": current_year,
        # REMOVER a linha antiga:
        # "current_month_display": _(current_date.strftime("%B %Y")).capitalize(),
        # ADICIONAR o objeto date:
        "current_date_obj": current_date,  # Passa o objeto date para o template
        "previous_month_url": previous_month_url,
        "next_month_url": next_month_url,
        "editing_mode": editing_mode,
        "default_date_value": default_date_value,
        "total_remuneration": total_remuneration,  # Remuneração do mês visualizado
    }
    return render(request, "escala/gerenciar_escala.html", context)


# --- View para Excluir Escala ---
@login_required
def excluir_escala(request, pk):
    """View para excluir uma escala específica."""
    escala = get_object_or_404(EscalaUsuario, pk=pk, usuario=request.user)

    if escala.confirmado_admin:
        messages.error(
            request,
            _("Não é possível excluir uma escala já confirmada pelo administrador."),
        )
    elif request.method == "POST":
        data_escala = escala.data
        try:
            escala.delete()
            messages.success(
                request,
                _("Escala de %(data)s excluída com sucesso.")
                % {"data": data_escala.strftime("%d/%m/%Y")},
            )
        except Exception as e:
            messages.error(request, _("Ocorreu um erro ao tentar excluir a escala."))
            # Logar erro 'e'
    else:
        # Se não for POST, redireciona de volta sem fazer nada
        messages.warning(
            request, _("A exclusão deve ser feita via confirmação no calendário.")
        )

    # Tenta usar o 'next' do POST, senão volta pro mês/ano da escala
    next_url = request.POST.get(
        "next",
        reverse("escala:gerenciar_escala")
        + f"?ano={escala.data.year}&mes={escala.data.month}",
    )
    return redirect(next_url)
