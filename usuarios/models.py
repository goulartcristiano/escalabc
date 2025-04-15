# usuarios/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
# Importe a validação de CPF (requer instalação: pip install python-brasil)
try:
    from validate_docbr import CPF
except ImportError:
    # Fornece um validador dummy se a biblioteca não estiver instalada
    # para permitir que as migrações iniciais funcionem.
    # Lembre-se de instalar python-brasil para validação real.
    print("AVISO: Biblioteca 'validate_docbr' não encontrada. Instale com 'pip install python-brasil' para validação de CPF.")
    class CPF:
        def validate(self, value):
            pass # Não faz nada sem a biblioteca

def validate_cpf_custom(value):
    """Valida o CPF usando validate_docbr."""
    cpf_validator = CPF()
    if not cpf_validator.validate(value):
        raise ValidationError('CPF inválido.')
    # Opcional: Formatar o CPF (ex: 123.456.789-00) - ajuste conforme necessário
    # return cpf_validator.mask(value) # Descomente se quiser armazenar formatado

class UsuarioManager(BaseUserManager):
    def create_user(self, cpf, password=None, **extra_fields):
        if not cpf:
            raise ValueError('O campo CPF é obrigatório.')

        # Normaliza o CPF removendo caracteres não numéricos antes de validar/salvar
        cpf = ''.join(filter(str.isdigit, cpf))
        # Validação pode ser feita aqui ou no model field
        # validate_cpf_custom(cpf) # Descomente se quiser validar aqui

        # Normaliza o email para minúsculas
        email = self.normalize_email(extra_fields.get('email'))
        extra_fields['email'] = email

        user = self.model(cpf=cpf, **extra_fields)
        user.set_password(password) # Criptografa a senha
        user.save(using=self._db)
        return user

    def create_superuser(self, cpf, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) # Superusuários devem ser ativos

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Garante que campos obrigatórios para superuser (definidos em REQUIRED_FIELDS)
        # tenham algum valor, mesmo que padrão, se não fornecidos.
        # Isso evita erros no comando createsuperuser.
        if 'nome_completo' not in extra_fields:
             extra_fields.setdefault('nome_completo', 'Admin') # Valor padrão
        if 'email' not in extra_fields:
             extra_fields.setdefault('email', f'{cpf}@example.com') # Valor padrão
        if 'data_nascimento' not in extra_fields:
             from datetime import date
             extra_fields.setdefault('data_nascimento', date.today()) # Valor padrão

        return self.create_user(cpf, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    nome_completo = models.CharField("Nome Completo", max_length=255)
    cpf = models.CharField(
        "CPF",
        max_length=11, # Apenas números
        unique=True,
        # validators=[validate_cpf_custom], # REMOVA OU COMENTE ESTA LINHA
        help_text="Digite apenas os números do CPF."
    )
    email = models.EmailField("Email", unique=True)
    data_nascimento = models.DateField("Data de Nascimento")
    is_active = models.BooleanField("Ativo", default=True)
    is_staff = models.BooleanField("Admin", default=False)

    # --- ADIÇÃO DO CAMPO FOTO ---
    foto = models.ImageField(
        "Foto de Perfil",
        upload_to='usuarios/fotos/', # Diretório dentro de MEDIA_ROOT
        blank=True,                  # Permite que o campo fique vazio
        null=True                    # Permite NULL no banco de dados
    )
    # --- FIM DA ADIÇÃO ---

    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['nome_completo', 'email', 'data_nascimento']

    objects = UsuarioManager() # Define o manager customizado

    def __str__(self):
        # Retorna nome_completo se existir, senão o CPF (username)
        return self.nome_completo or self.cpf

    def clean(self):
        """
        Garante que o CPF seja limpo (apenas números) antes de salvar.
        """
        super().clean()
        if self.cpf:
            self.cpf = ''.join(filter(str.isdigit, self.cpf))

    # Opcional: Propriedade para exibir CPF formatado
    @property
    def cpf_formatado(self):
        if self.cpf and len(self.cpf) == 11:
            return f"{self.cpf[:3]}.{self.cpf[3:6]}.{self.cpf[6:9]}-{self.cpf[9:]}"
        return self.cpf

    # Opcional: Método para deletar foto antiga ao salvar uma nova
    def save(self, *args, **kwargs):
         try:
             this = Usuario.objects.get(id=self.id)
             if this.foto != self.foto:
                 this.foto.delete(save=False)
         except: pass # Objeto é novo, ainda não tem o campo foto.
         super(Usuario, self).save(*args, **kwargs)

    # Opcional: Método para deletar o arquivo da foto quando o usuário for deletado
    def delete(self, *args, **kwargs):
         self.foto.delete(save=False)
         super(Usuario, self).delete(*args, **kwargs)
