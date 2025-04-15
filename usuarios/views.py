# usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Usuario
from .forms import LoginForm, UserProfileEditForm, CustomPasswordChangeForm
import os # Necessário para deletar arquivos

# ... (user_login e user_logout permanecem iguais) ...
def user_login(request):
    if request.user.is_authenticated:
        return redirect('escala:gerenciar_escala')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cpf = form.cleaned_data['cpf']
            password = form.cleaned_data['password']
            user = authenticate(request, cpf=cpf, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    next_url = request.GET.get('next', 'escala:gerenciar_escala')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Esta conta está desativada.')
            else:
                messages.error(request, 'CPF ou senha inválidos.')
        else:
            # Adiciona erros do formulário às mensagens se houver
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
            # Mensagem genérica caso não haja erros específicos de campo (raro)
            if not form.errors:
                 messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = LoginForm()

    return render(request, 'usuarios/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'Você saiu com sucesso.')
    return redirect('login')


@login_required
def edit_profile(request):
    user = request.user
    old_foto_path = user.foto.path if user.foto else None

    if request.method == 'POST':
        profile_form = UserProfileEditForm(request.POST, request.FILES, instance=user)
        # Instancia o form de senha sempre
        password_form = CustomPasswordChangeForm(user, request.POST)

        # Verifica se houve tentativa de mudar a senha
        password_change_attempted = bool(request.POST.get('old_password') or \
                                         request.POST.get('new_password1') or \
                                         request.POST.get('new_password2'))

        # --- CORREÇÃO: Define password_valid em todos os casos ---
        if password_change_attempted:
            password_valid = password_form.is_valid()
        else:
            # Se não tentou mudar, consideramos válido para não bloquear o save do perfil
            password_valid = True
            # E garantimos que os campos não sejam marcados como required no re-render
            for field in password_form.fields.values():
                field.required = False
        # --- FIM DA CORREÇÃO ---

        profile_valid = profile_form.is_valid()

        # Agora a condição usa variáveis sempre definidas
        if profile_valid and password_valid:
            # Lógica de exclusão da foto antiga (mantida da sugestão anterior)
            foto_cleared = request.POST.get(f'{profile_form.prefix}-foto-clear' if profile_form.prefix else 'foto-clear') == 'on'
            new_foto_uploaded = request.FILES.get('foto')

            if old_foto_path and (foto_cleared or new_foto_uploaded):
                 if os.path.isfile(old_foto_path):
                     try:
                         os.remove(old_foto_path)
                     except OSError as e:
                         print(f"Erro ao deletar foto antiga {old_foto_path}: {e}")
                         messages.warning(request, "Não foi possível remover o arquivo da foto antiga.")

            # Salva o formulário de perfil
            profile_form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')

            # Salva a senha APENAS se a mudança foi tentada E válida
            if password_change_attempted and password_valid:
                password_user = password_form.save()
                update_session_auth_hash(request, password_user)
                messages.success(request, 'Sua senha foi alterada com sucesso!')

            return redirect('edit_profile')

        else:
            # Se chegou aqui, houve erro de validação
            if not profile_valid:
                 messages.error(request, 'Erro ao atualizar o perfil. Verifique os campos marcados.')
                 # Adiciona erros específicos do profile_form às mensagens
                 for field, errors in profile_form.errors.items():
                     label = profile_form.fields[field].label or field
                     messages.error(request, f"{label}: {', '.join(errors)}")

            # Se a tentativa de senha falhou, password_valid será False
            if password_change_attempted and not password_valid:
                 messages.error(request, 'Erro ao alterar a senha. Verifique os campos marcados.')
                 # Adiciona erros específicos do password_form às mensagens
                 for field, errors in password_form.errors.items():
                     label = password_form.fields[field].label or field
                     messages.error(request, f"{label}: {', '.join(errors)}")

            # Garante que se a tentativa de senha NÃO ocorreu, os campos não apareçam como erro
            if not password_change_attempted:
                 password_form = CustomPasswordChangeForm(user) # Recria sem dados POST
                 for field in password_form.fields.values():
                     field.required = False


    else: # Método GET
        profile_form = UserProfileEditForm(instance=user)
        password_form = CustomPasswordChangeForm(user)
        # Define campos de senha como não obrigatórios na exibição inicial
        for field in password_form.fields.values():
            field.required = False

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
        'user': user
    }
    return render(request, 'usuarios/edit_profile.html', context)
