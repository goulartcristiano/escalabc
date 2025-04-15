# usuarios/admin.py
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import IntegrityError
from django import forms
from .models import Usuario
from .forms import UserCreationForm, UserChangeForm


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    # Usa os forms customizados
    form = UserChangeForm
    add_form = UserCreationForm

    # Configurações de listagem (parecem OK)
    list_display = (
        "cpf",
        "nome_completo",
        "email",
        "data_nascimento",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    list_display_links = ("cpf", "nome_completo", "email")
    search_fields = ("cpf", "nome_completo", "email")
    ordering = ("nome_completo",)
    list_filter = ("is_active", "is_staff", "is_superuser")

    # Campos exibidos no formulário de EDIÇÃO
    fieldsets = (
        (None, {"fields": ("cpf", "password")}),
        (
            "Informações Pessoais",
            {"fields": ("nome_completo", "email", "data_nascimento")},
        ),
        (
            "Permissões",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        # --- CORREÇÃO AQUI ---
        # Remova 'date_joined', pois não existe em AbstractBaseUser
        ("Datas Importantes", {"fields": ("last_login",)}),
        # --- FIM DA CORREÇÃO ---
    )

    # Campos exibidos no formulário de CRIAÇÃO
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "cpf",
                    "nome_completo",
                    "email",
                    "data_nascimento",
                    "password",
                    "password2",
                ),
            },
        ),
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    # Método save_model (parece OK)
    def save_model(self, request, obj, form, change):
        """
        Sobrescreve para capturar IntegrityError e fornecer feedback melhor.
        """
        try:
            print(
                f"--- [Admin Save] Tentando salvar: CPF={form.cleaned_data.get('cpf')}, Email={form.cleaned_data.get('email')} ---"
            )
            # No caso de criação (not change), o form é UserCreationForm, que já faz o hash no save()
            # No caso de alteração (change=True), o form é UserChangeForm, que não lida com senha.
            # A senha só é alterada pela view específica de mudança de senha do admin.
            # Portanto, a chamada a super().save_model deve ser suficiente aqui.
            super().save_model(request, obj, form, change)
            print("--- [Admin Save] Salvo com sucesso ---")

        except IntegrityError as e:
            print(f"--- [Admin Save] ERRO DE INTEGRIDADE: {e} ---")
            error_message = "Erro ao salvar: "
            if "usuarios_usuario_cpf_key" in str(
                e
            ) or "UNIQUE constraint failed: usuarios_usuario.cpf" in str(e):
                error_message += "Este CPF já está cadastrado."
                form.add_error("cpf", forms.ValidationError(error_message))
            elif "usuarios_usuario_email_key" in str(
                e
            ) or "UNIQUE constraint failed: usuarios_usuario.email" in str(e):
                error_message += "Este Email já está cadastrado."
                form.add_error("email", forms.ValidationError(error_message))
            else:
                error_message += f"Conflito de dados no banco de dados ({e})."
                form.add_error(None, forms.ValidationError(error_message))
            messages.error(request, error_message)

        except Exception as e:
            print(
                f"--- [Admin Save] ERRO INESPERADO em save_model: {type(e).__name__}: {e} ---"
            )
            import traceback

            traceback.print_exc()
            messages.error(request, f"Ocorreu um erro inesperado ao salvar: {e}")
            form.add_error(
                None, forms.ValidationError(f"Ocorreu um erro inesperado: {e}")
            )
