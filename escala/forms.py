# /home/cristiano/dev/python/escalabc/escala/forms.py

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import EscalaUsuario, TurnoEscolha
from datetime import date


class EscalaForm(forms.ModelForm):
    # Define os turnos que o usuário pode escolher explicitamente
    turno = forms.ChoiceField(
        choices=[
            ("", "---------"),  # Opção vazia
            (TurnoEscolha.DIA.value, TurnoEscolha.DIA.label),
            (TurnoEscolha.NOITE.value, TurnoEscolha.NOITE.label),
            (TurnoEscolha.INTEIRO.value, TurnoEscolha.INTEIRO.label),
        ],
        required=True,
        label=_("Turno"),
        # Adiciona classe para estilização se necessário
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = EscalaUsuario
        fields = ["data", "turno"]  # Campos que o usuário pode preencher
        widgets = {
            "data": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            # 'turno' já foi definido acima como ChoiceField com widget Select
        }
        labels = {
            "data": _("Data"),
        }

    def __init__(self, *args, **kwargs):
        # Pega o usuário passado pela view (se houver)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Se estiver editando (instance is not None), torna o campo data readonly
        if self.instance and self.instance.pk:
            self.fields["data"].widget.attrs["readonly"] = True
            self.fields["data"].widget.attrs["title"] = _(
                "Data não pode ser alterada durante a edição"
            )
            # Adiciona classe CSS para estilo readonly se não existir
            css_class = self.fields["data"].widget.attrs.get("class", "")
            if "readonly-input" not in css_class:
                self.fields["data"].widget.attrs["class"] = (
                    css_class + " readonly-input"
                ).strip()

        # Define o valor inicial do turno se estiver editando (redundante com a view, mas seguro)
        # CORREÇÃO: Comparar com os values das choices
        if self.instance and self.instance.pk and self.instance.turno:
            turnos_permitidos_values = [
                TurnoEscolha.DIA.value,
                TurnoEscolha.NOITE.value,
                TurnoEscolha.INTEIRO.value,
            ]
            if self.instance.turno in turnos_permitidos_values:
                self.initial["turno"] = self.instance.turno

    def clean_data(self):
        """Validação adicional para o campo data."""
        data_selecionada = self.cleaned_data.get("data")
        if data_selecionada and data_selecionada < date.today():
            # Exemplo: Não permitir adicionar/editar escalas para datas passadas
            # Você pode ajustar esta lógica conforme necessário
            # raise forms.ValidationError(_("Não é possível adicionar ou modificar escalas para datas passadas."))
            pass  # Comentado para permitir datas passadas por enquanto

        # Se estiver criando (não editando), verifica se já existe escala para o usuário/data
        if not self.instance or not self.instance.pk:
            if data_selecionada and self.user:
                if EscalaUsuario.objects.filter(
                    usuario=self.user, data=data_selecionada
                ).exists():
                    raise forms.ValidationError(
                        _(
                            "Você já possui uma escala para esta data. Use o botão Editar no calendário."
                        )
                    )
        return data_selecionada  # Retorna o valor limpo

    def clean_turno(self):
        """Garante que o turno selecionado é permitido para o usuário."""
        turno_selecionado = self.cleaned_data.get("turno")
        turnos_permitidos_usuario = [
            TurnoEscolha.DIA.value,
            TurnoEscolha.NOITE.value,
            TurnoEscolha.INTEIRO.value,
        ]
        if turno_selecionado not in turnos_permitidos_usuario:
            raise forms.ValidationError(_("Turno inválido selecionado."))
        return turno_selecionado  # Retorna o valor limpo

    def save(self, commit=True):
        """Sobrescreve save para garantir associação com usuário."""
        instance = super().save(commit=False)
        if self.user:
            # --- CORREÇÃO PRINCIPAL AQUI ---
            instance.usuario = self.user  # Associa ao campo 'usuario' do modelo
            # --- FIM DA CORREÇÃO ---
        if commit:
            instance.save()
            # Se houver ManyToMany fields, eles seriam salvos aqui com self.save_m2m()
        return instance
