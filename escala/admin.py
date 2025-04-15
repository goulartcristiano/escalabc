# escala/admin.py

import calendar
import json
from datetime import date, timedelta

from django.contrib import admin, messages
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect

# --- Importar ValorTurno ---
from .models import EscalaUsuario, TurnoEscolha, ValorTurno

User = get_user_model()
csrf_protect_m = method_decorator(csrf_protect)
NOME_GRUPO_OCULTO = "Oculto da Escala"


# Função auxiliar (sem alterações)
def get_escala_data_for_month(year, month):
    items = (
        EscalaUsuario.objects.filter(data__year=year, data__month=month)
        .select_related("usuario")
        .order_by("usuario__nome_completo", "turno")
    )
    data_by_day = {}
    for item in items:
        dia = item.data
        if dia not in data_by_day:
            data_by_day[dia] = {"interessados": [], "confirmados": []}
        if item.confirmado_admin:
            data_by_day[dia]["confirmados"].append(item)
        else:
            data_by_day[dia]["interessados"].append(item)
    return data_by_day


# Classe CalendarChangeList (sem alterações)
class CalendarChangeList(ChangeList):
    pass


@admin.register(EscalaUsuario)
class EscalaUsuarioAdmin(admin.ModelAdmin):
    # --- MODIFICAÇÃO: Adicionado 'valor_turno_display' ---
    list_display = (
        "usuario_nome_completo",
        "data",
        "turno",
        "confirmado_admin",
        "valor_turno_display",
        "criado_em",
    )
    list_filter = ("confirmado_admin", "turno", "data", "usuario__nome_completo")
    search_fields = (
        "usuario__nome_completo",
        "usuario__email",
        "usuario__cpf",
    )  # Mantido CPF
    ordering = ("-data", "usuario__nome_completo")
    list_per_page = 25
    change_list_template = "admin/escala/escalausuario/change_list_calendar.html"
    # Opcional: Melhora performance se houver muitos usuários
    raw_id_fields = ("usuario",)

    # Método para exibir o nome completo na lista (sem alterações)
    @admin.display(description=_("Usuário"), ordering="usuario__nome_completo")
    def usuario_nome_completo(self, obj):
        return obj.usuario.nome_completo or obj.usuario.email

    # --- NOVO MÉTODO para exibir o valor do turno formatado ---
    @admin.display(description=_("Valor Turno (R$)"), ordering="turno")
    def valor_turno_display(self, obj):
        # Este método agora usará o valor buscado do banco de dados
        # pela property obj.valor_turno
        try:
            return f"{obj.valor_turno:.2f}"
        except TypeError:  # Caso valor_turno retorne None ou algo não formatável
            return "N/A"

    # --- FIM DO NOVO MÉTODO ---

    # Métodos changelist_view, response_change, get_urls, confirmar_escala_view,
    # adicionar_escala_view, editar_escala_redirect_view (sem alterações na lógica principal)
    # Apenas garantindo que as mensagens de sucesso sejam adicionadas corretamente
    def changelist_view(self, request, extra_context=None):
        # ... (código mantido como antes) ...
        view_param = request.GET.get("view")
        is_calendar = view_param == "calendar"
        context_update = extra_context or {}
        context_update["is_calendar_view"] = is_calendar
        context_update["show_calendar_view_link"] = True
        opts = self.model._meta
        context_update["opts"] = opts

        if is_calendar:
            try:
                today = date.today()
                try:
                    year = int(request.GET.get("year", today.year))
                    month = int(request.GET.get("month", today.month))
                    if not (1 <= month <= 12):
                        raise ValueError("Mês inválido")
                    if not (1900 < year < 2100):
                        raise ValueError("Ano inválido")
                    current_month_date = date(year, month, 1)
                except (ValueError, TypeError):
                    year = today.year
                    month = today.month
                    current_month_date = date(year, month, 1)

                escala_data = get_escala_data_for_month(year, month)
                confirmed_user_ids_by_day = {}
                interested_user_ids_by_day = {}
                for day, data in escala_data.items():
                    confirmed_user_ids_by_day[day] = {
                        item.usuario_id for item in data["confirmados"]
                    }
                    interested_user_ids_by_day[day] = {
                        item.usuario_id for item in data["interessados"]
                    }

                try:
                    Group.objects.get(name=NOME_GRUPO_OCULTO)
                    all_users = (
                        User.objects.filter(is_active=True)
                        .exclude(groups__name=NOME_GRUPO_OCULTO)
                        .order_by("nome_completo")
                    )
                except Group.DoesNotExist:
                    print(
                        f"AVISO (Admin View): Grupo '{NOME_GRUPO_OCULTO}' não encontrado."
                    )
                    all_users = User.objects.filter(is_active=True).order_by(
                        "nome_completo"
                    )

                cal = calendar.Calendar(firstweekday=6)
                month_days_list = list(cal.itermonthdates(year, month))
                prev_month_dt = current_month_date - timedelta(days=1)
                next_month_dt = (
                    current_month_date.replace(day=28) + timedelta(days=4)
                ).replace(day=1)

                context_update.update(
                    {
                        "title": _("Calendário de Escalas"),
                        "escala_data_by_day": escala_data,
                        "confirmed_user_ids_by_day": confirmed_user_ids_by_day,
                        "interested_user_ids_by_day": interested_user_ids_by_day,
                        "all_eligible_users": all_users,
                        "month_days": month_days_list,
                        "current_year": year,
                        "current_month": month,
                        "prev_month_url_params": f"?view=calendar&year={prev_month_dt.year}&month={prev_month_dt.month}",
                        "next_month_url_params": f"?view=calendar&year={next_month_dt.year}&month={next_month_dt.month}",
                        "list_view_url": reverse(
                            f"admin:{opts.app_label}_{opts.model_name}_changelist"
                        ),
                    }
                )
            except Exception as e:
                print(f"Erro ao calcular dados do calendário: {e}")
                context_update["is_calendar_view"] = False
                is_calendar = False
                messages.error(request, _("Ocorreu um erro ao gerar o calendário."))

        original_get = request.GET
        mutable_get = request.GET.copy()
        mutable_get.pop("view", None)
        mutable_get.pop("year", None)
        mutable_get.pop("month", None)
        request.GET = mutable_get
        response = None
        try:
            response = super().changelist_view(request, extra_context=context_update)
        finally:
            request.GET = original_get

        if hasattr(response, "context_data"):
            response.context_data["is_calendar_view"] = is_calendar
            response.context_data["opts"] = opts
            response.context_data["show_calendar_view_link"] = True
            if is_calendar and "all_eligible_users" not in response.context_data:
                response.context_data.update(context_update)
        return response

    def response_change(self, request, obj):
        # ... (código mantido como antes) ...
        if "_save" in request.POST:
            opts = self.model._meta
            year = obj.data.year
            month = obj.data.month
            changelist_url = reverse(
                f"admin:{opts.app_label}_{opts.model_name}_changelist"
            )
            target_url = f"{changelist_url}?view=calendar&year={year}&month={month}"
            user_display = obj.usuario.nome_completo or obj.usuario.get_username()
            self.message_user(
                request,
                f"Escala de {user_display} para {obj.data.strftime('%d/%m/%Y')} salva com sucesso.",
                messages.SUCCESS,
            )
            return HttpResponseRedirect(target_url)
        else:
            return super().response_change(request, obj)

    def get_urls(self):
        # ... (código mantido como antes) ...
        urls = super().get_urls()
        opts = self.model._meta
        info = opts.app_label, opts.model_name
        custom_urls = [
            path(
                "ajax/confirmar-escala/",
                self.admin_site.admin_view(self.confirmar_escala_view),
                name="%s_%s_confirmar" % info,
            ),
            path(
                "ajax/adicionar-escala/",
                self.admin_site.admin_view(self.adicionar_escala_view),
                name="%s_%s_adicionar" % info,
            ),
            path(
                "ajax/editar-escala/<int:user_id>/<str:date_str>/",
                self.admin_site.admin_view(self.editar_escala_redirect_view),
                name="%s_%s_editar_redirect" % info,
            ),
        ]
        return custom_urls + urls

    @csrf_protect_m
    @transaction.atomic
    def confirmar_escala_view(self, request):
        # ... (código mantido como antes, incluindo messages.success) ...
        opts = self.model._meta
        if not request.method == "POST":
            return JsonResponse(
                {"status": "error", "message": "Método inválido"}, status=405
            )
        if not request.user.has_perm(f"{opts.app_label}.change_{opts.model_name}"):
            return JsonResponse(
                {"status": "error", "message": "Permissão negada"}, status=403
            )

        try:
            req_data = json.loads(request.body)
            user_id = int(req_data.get("userId"))
            date_str = req_data.get("date")
            target_date = date.fromisoformat(date_str)
            user_alvo = get_object_or_404(User, pk=user_id)

            try:
                grupo_oculto = Group.objects.get(name=NOME_GRUPO_OCULTO)
                if user_alvo.groups.filter(pk=grupo_oculto.pk).exists():
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": f"Usuário '{user_alvo.get_username()}' pertence ao grupo '{NOME_GRUPO_OCULTO}'.",
                        },
                        status=400,
                    )
            except Group.DoesNotExist:
                pass

            escala = get_object_or_404(
                EscalaUsuario, usuario=user_alvo, data=target_date
            )
            escala.confirmado_admin = True
            escala.save(update_fields=["confirmado_admin"])

            user_display_name = user_alvo.nome_completo or user_alvo.get_username()
            success_message = f"Escala de {user_display_name} para {target_date.strftime('%d/%m/%Y')} confirmada com sucesso!"

            messages.success(request, success_message)

            return JsonResponse(
                {
                    "status": "success",
                    "message": success_message,
                    "userId": user_id,
                    "date": date_str,
                    "turno": escala.turno,
                    "turnoDisplay": escala.get_turno_display(),
                    "userName": user_display_name,
                }
            )
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            return JsonResponse(
                {"status": "error", "message": f"Dados inválidos: {e}"}, status=400
            )
        except User.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Usuário alvo não encontrado"},
                status=404,
            )
        except EscalaUsuario.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Registro de escala não encontrado."},
                status=404,
            )
        except Exception as e:
            print(f"Erro em confirmar_escala_view: {e}")
            return JsonResponse(
                {"status": "error", "message": "Erro interno do servidor."}, status=500
            )

    @csrf_protect_m
    @transaction.atomic
    def adicionar_escala_view(self, request):
        # ... (código mantido como antes, incluindo messages.success) ...
        opts = self.model._meta
        if not request.method == "POST":
            return JsonResponse(
                {"status": "error", "message": "Método inválido"}, status=405
            )
        if not request.user.has_perm(f"{opts.app_label}.add_{opts.model_name}"):
            return JsonResponse(
                {"status": "error", "message": "Permissão negada"}, status=403
            )

        try:
            req_data = json.loads(request.body)
            user_id = int(req_data.get("userId"))
            date_str = req_data.get("date")
            turno_selecionado = req_data.get("turno", TurnoEscolha.DIA)
            if turno_selecionado not in TurnoEscolha.values:
                turno_selecionado = TurnoEscolha.DIA

            target_date = date.fromisoformat(date_str)
            user_alvo = get_object_or_404(User, pk=user_id)

            try:
                grupo_oculto = Group.objects.get(name=NOME_GRUPO_OCULTO)
                if user_alvo.groups.filter(pk=grupo_oculto.pk).exists():
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": f"Usuário '{user_alvo.get_username()}' pertence ao grupo '{NOME_GRUPO_OCULTO}'.",
                        },
                        status=400,
                    )
            except Group.DoesNotExist:
                pass

            escala, created = EscalaUsuario.objects.update_or_create(
                usuario=user_alvo,
                data=target_date,
                defaults={"confirmado_admin": True, "turno": turno_selecionado},
            )

            user_display_name = user_alvo.nome_completo or user_alvo.get_username()
            if created:
                success_message = f"Usuário {user_display_name} adicionado e confirmado ({escala.get_turno_display()}) para {target_date.strftime('%d/%m/%Y')}!"
            else:
                success_message = f"Escala de {user_display_name} atualizada e confirmada ({escala.get_turno_display()}) para {target_date.strftime('%d/%m/%Y')}."

            messages.success(request, success_message)

            return JsonResponse(
                {
                    "status": "success",
                    "message": success_message,
                    "created": created,
                    "userId": user_id,
                    "date": date_str,
                    "turno": escala.turno,
                    "turnoDisplay": escala.get_turno_display(),
                    "userName": user_display_name,
                }
            )
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            return JsonResponse(
                {"status": "error", "message": f"Dados inválidos: {e}"}, status=400
            )
        except User.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Usuário alvo não encontrado"},
                status=404,
            )
        except Exception as e:
            print(f"Erro em adicionar_escala_view: {e}")
            return JsonResponse(
                {"status": "error", "message": "Erro interno do servidor."}, status=500
            )

    def editar_escala_redirect_view(self, request, user_id, date_str):
        # ... (código mantido como antes) ...
        opts = self.model._meta
        if not request.user.has_perm(f"{opts.app_label}.change_{opts.model_name}"):
            messages.error(request, _("Você não tem permissão para editar escalas."))
            changelist_url = reverse(
                f"admin:{opts.app_label}_{opts.model_name}_changelist"
            )
            year, month = date.today().year, date.today().month
            try:
                target_date_temp = date.fromisoformat(date_str)
                year, month = target_date_temp.year, target_date_temp.month
            except ValueError:
                pass
            return redirect(f"{changelist_url}?view=calendar&year={year}&month={month}")

        try:
            target_date = date.fromisoformat(date_str)
            escala_obj = get_object_or_404(
                EscalaUsuario, usuario_id=user_id, data=target_date
            )
            change_url = reverse(
                f"admin:{opts.app_label}_{opts.model_name}_change", args=[escala_obj.pk]
            )
            return redirect(change_url)
        except (ValueError, EscalaUsuario.DoesNotExist):
            messages.warning(
                request, _("Não foi possível encontrar a escala para editar.")
            )
            calendar_url = reverse(
                f"admin:{opts.app_label}_{opts.model_name}_changelist"
            )
            year, month = date.today().year, date.today().month
            try:
                target_date_temp = date.fromisoformat(date_str)
                year, month = target_date_temp.year, target_date_temp.month
            except ValueError:
                pass
            return redirect(f"{calendar_url}?view=calendar&year={year}&month={month}")
        except Exception as e:
            messages.error(
                request, _("Ocorreu um erro inesperado ao tentar editar a escala.")
            )
            print(f"Erro em editar_escala_redirect_view: {e}")
            changelist_url = reverse(
                f"admin:{opts.app_label}_{opts.model_name}_changelist"
            )
            return redirect(changelist_url)


# --- NOVO ADMIN PARA ValorTurno ---
@admin.register(ValorTurno)
class ValorTurnoAdmin(admin.ModelAdmin):
    list_display = ("get_turno_display", "valor", "descricao", "atualizado_em")
    # Campos editáveis no formulário (não inclui a chave primária 'turno_codigo')
    # fields = ('valor', 'descricao') # Removido para usar get_fields
    # Apenas o valor e a descrição podem ser editados na lista
    list_editable = ("valor", "descricao")

    # Não permitir adicionar novos tipos de turno (já definidos em TurnoEscolha)
    def has_add_permission(self, request):
        return False

    # Não permitir deletar (apenas editar o valor)
    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description=_("Turno"), ordering="turno_codigo")
    def get_turno_display(self, obj):
        # Mostra o nome amigável do turno
        try:
            return TurnoEscolha(obj.turno_codigo).label
        except ValueError:
            return obj.turno_codigo  # Fallback

    # Garante que o admin veja todos os campos ao editar
    def get_fields(self, request, obj=None):
        if obj:  # Editando
            # Mostra o código (readonly) e os campos editáveis
            return ("turno_codigo", "valor", "descricao", "atualizado_em")
        # Não deve chegar aqui pois has_add_permission é False
        return super().get_fields(request, obj)

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando
            # Torna o código e a data de atualização readonly
            return ("turno_codigo", "atualizado_em")
        # Não deve chegar aqui
        return ("atualizado_em",)


# --- FIM DO NOVO ADMIN ---
