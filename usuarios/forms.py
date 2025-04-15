# /home/cristiano/dev/python/escalabc/usuarios/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm,
    UserChangeForm,
    PasswordChangeForm,
    AuthenticationForm,
)
from django.utils.translation import gettext_lazy as _

User = get_user_model()

# --- Formulários para o ADMIN ---


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "cpf",
            "email",
            "nome_completo",
            "data_nascimento",
        )
        labels = {
            "cpf": _("CPF (apenas números)"),
            "nome_completo": _("Nome Completo"),
            "data_nascimento": _("Data de Nascimento"),
        }
        # Mantém o widget na criação para facilitar
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
        }


class CustomUserChangeForm(UserChangeForm):
    password = None

    class Meta(UserChangeForm.Meta):
        model = User
        fields = (
            "cpf",
            "email",
            "nome_completo",
            "data_nascimento",  # Campo está aqui
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
        )
        labels = {
            "cpf": _("CPF"),
            "nome_completo": _("Nome Completo"),
            "data_nascimento": _("Data de Nascimento"),
        }
        # --- MODIFICAÇÃO: Removemos o widget específico para teste ---
        widgets = {
            "cpf": forms.TextInput(attrs={"readonly": "readonly"}),
            # "data_nascimento": forms.DateInput(attrs={"type": "date"}), # LINHA COMENTADA/REMOVIDA
        }
        # --- FIM DA MODIFICAÇÃO ---


# --- Formulários para as VIEWS (Mantidos como antes) ---


class LoginForm(forms.Form):
    cpf = forms.CharField(
        label=_("CPF"),
        max_length=14,
        widget=forms.TextInput(
            attrs={"placeholder": "Digite seu CPF", "class": "form-control"}
        ),
    )
    password = forms.CharField(
        label=_("Senha"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": "Digite sua senha", "class": "form-control"}
        ),
    )

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf")
        if cpf:
            return "".join(filter(str.isdigit, cpf))
        return cpf


class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["nome_completo", "email", "data_nascimento", "foto"]
        labels = {
            "nome_completo": _("Nome Completo"),
            "email": _("Email"),
            "data_nascimento": _("Data de Nascimento"),
            "foto": _("Foto de Perfil"),
        }
        widgets = {
            "data_nascimento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "nome_completo": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "foto": forms.ClearableFileInput(attrs={"class": "form-control-file"}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label=_("Senha atual"),
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "autofocus": False,
                "class": "form-control",
            }
        ),
        strip=False,
    )
    new_password1 = forms.CharField(
        label=_("Nova senha"),
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "class": "form-control"}
        ),
        strip=False,
    )
    new_password2 = forms.CharField(
        label=_("Confirmação da nova senha"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={"autocomplete": "new-password", "class": "form-control"}
        ),
    )
