# escala/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator  # Importar MinValueValidator


# Classe TurnoEscolha (definição dos choices permanece a mesma)
class TurnoEscolha(models.TextChoices):
    DIA = "D", _("Dia (12h)")
    NOITE = "N", _("Noite (12h)")
    INTEIRO = "I", _("Inteiro (24h)")
    MANHA = "M", _("Manhã (6h)")
    TARDE = "T", _("Tarde (6h)")
    MADRUGADA = "A", _("Madrugada (6h)")

    # --- MÉTODO get_valor MODIFICADO ---
    @classmethod
    def get_valor(cls, turno_code):
        """Busca o valor atual do turno no modelo ValorTurno."""
        try:
            # Busca o objeto ValorTurno correspondente ao código
            # Usamos .get() que levanta DoesNotExist se não encontrar
            valor_turno_obj = ValorTurno.objects.get(turno_codigo=turno_code)
            return valor_turno_obj.valor
        except ValorTurno.DoesNotExist:
            # Fallback: Se o valor não foi cadastrado no admin ainda
            print(
                f"AVISO: Valor para o turno '{turno_code}' não encontrado na tabela ValorTurno. Usando R$ 0.00."
            )
            return Decimal("0.00")
        except Exception as e:
            # Captura outros erros de banco de dados
            print(f"ERRO ao buscar valor do turno '{turno_code}': {e}")
            return Decimal("0.00")

    # --- FIM DA MODIFICAÇÃO ---


# --- NOVO MODELO PARA ARMAZENAR OS VALORES BASE DOS TURNOS ---
class ValorTurno(models.Model):
    turno_codigo = models.CharField(
        _("Código do Turno"),
        max_length=1,
        choices=TurnoEscolha.choices,
        unique=True,  # Garante um valor por tipo de turno
        primary_key=True,  # Usa o código como chave primária
    )
    valor = models.DecimalField(
        _("Valor Atual (R$)"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],  # Garante valor positivo
        help_text=_("Valor base atual para este tipo de turno."),
    )
    descricao = models.CharField(
        _("Descrição/Observação"),
        max_length=100,
        blank=True,
        help_text=_('Opcional: Ex: "Valor reajustado em 01/2026"'),
    )
    atualizado_em = models.DateTimeField(_("Última Atualização"), auto_now=True)

    class Meta:
        verbose_name = _("Valor de Turno")
        verbose_name_plural = _("Valores dos Turnos")
        ordering = ["turno_codigo"]

    def __str__(self):
        # Usa o label do TurnoEscolha para exibição amigável
        # Precisamos instanciar para acessar o label
        try:
            turno_display = TurnoEscolha(self.turno_codigo).label
        except ValueError:
            turno_display = self.turno_codigo  # Fallback se o código for inválido
        return f"{turno_display}: R$ {self.valor:.2f}"


# --- FIM DO NOVO MODELO ---


# Modelo EscalaUsuario (sem alterações na estrutura, mas usa o novo valor_turno)
class EscalaUsuario(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="escalas_usuario",
        verbose_name=_("Usuário"),
    )
    data = models.DateField(verbose_name=_("Data"))
    turno = models.CharField(
        max_length=1, choices=TurnoEscolha.choices, verbose_name=_("Turno")
    )
    confirmado_admin = models.BooleanField(
        default=False, verbose_name=_("Confirmado pelo Admin")
    )
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name=_("Criado em"))
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name=_("Atualizado em"))

    class Meta:
        verbose_name = _("Escala do Usuário")
        verbose_name_plural = _("Escalas dos Usuários")
        unique_together = ("usuario", "data")
        ordering = ["data", "usuario"]

    def __str__(self):
        nome_usuario = self.usuario.nome_completo or self.usuario.email
        return f"{nome_usuario} - {self.data.strftime('%d/%m/%Y')} ({self.get_turno_display()})"

    @property
    def valor_turno(self):
        """Retorna o valor monetário (Decimal) para o turno desta escala."""
        # Este método agora usa o TurnoEscolha.get_valor() modificado
        # que busca o valor do modelo ValorTurno no banco de dados.
        return TurnoEscolha.get_valor(self.turno)

    def clean(self):
        pass

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
