// static/escala/js/admin_calendar_actions.js
document.addEventListener('DOMContentLoaded', function() {
    const calendarContainer = document.querySelector('.calendar-grid-container');
    const csrftoken = getCookie('csrftoken');

    let confirmUrl = null;
    let addUrl = null;
    const urlScriptTag = document.getElementById('calendar-urls');

    if (urlScriptTag) {
        try {
            const urls = JSON.parse(urlScriptTag.textContent);
            confirmUrl = urls.confirmUrl;
            addUrl = urls.addUrl;
            console.log("Admin Calendar JS: URLs carregadas:", urls);
        } catch (e) {
            console.error("Admin Calendar JS: Erro ao parsear URLs do JSON:", e);
        }
    } else {
        console.error("Admin Calendar JS: Elemento <script id='calendar-urls'> não encontrado.");
    }

    if (!calendarContainer || !csrftoken || !confirmUrl || !addUrl) {
        if (!calendarContainer) console.error("Admin Calendar JS: Elemento .calendar-grid-container não encontrado.");
        if (!csrftoken) console.error("Admin Calendar JS: CSRF token não encontrado.");
        if (!confirmUrl || !addUrl) console.error("Admin Calendar JS: URLs das ações não foram carregadas.");
        return;
    }

    console.log("Admin Calendar JS: Inicializado com sucesso. Adicionando listener de clique.");

    calendarContainer.addEventListener('click', function(event) {
        const target = event.target;
        const confirmButton = target.closest('.confirm-scale-btn');
        const addButton = target.closest('.add-scale-btn');
        const dayCell = target.closest('.calendar-day.current-month');

        if (!dayCell) return;
        const date = dayCell.dataset.date;
        if (!date) {
            console.error("Admin Calendar JS: Atributo data-date não encontrado na célula:", dayCell);
            return;
        }

        if (confirmButton) {
            const userSelect = dayCell.querySelector('.user-select-day');
            if (!userSelect || !userSelect.value) {
                alert('Por favor, selecione um usuário interessado para confirmar.');
                return;
            }
            const userId = userSelect.value;
            console.log(`Admin Calendar JS: Confirmar User ID: ${userId} no dia ${date}`);
            sendScaleAction(confirmUrl, { userId, date }, csrftoken, confirmButton);
        }
        else if (addButton) {
            const addUserSelect = dayCell.querySelector('.add-user-select');
            if (!addUserSelect || !addUserSelect.value) {
                alert('Por favor, selecione um usuário da lista para adicionar.');
                return;
            }
            const userId = addUserSelect.value;
            console.log(`Admin Calendar JS: Adicionar User ID: ${userId} no dia ${date}`);
            sendScaleAction(addUrl, { userId, date }, csrftoken, addButton);
        }
    });

    function sendScaleAction(url, data, csrfToken, buttonElement) {
        console.log("Admin Calendar JS: Enviando ação AJAX:", url, data);
        buttonElement.disabled = true;
        buttonElement.textContent = 'Processando...';

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            console.log("Admin Calendar JS: Resposta recebida, Status:", response.status);
            if (!response.ok) {
                return response.json().then(errData => {
                    console.error("Admin Calendar JS: Erro na resposta (JSON):", errData);
                    throw new Error(errData.message || `Erro ${response.status}`);
                }).catch((jsonError) => {
                    console.error("Admin Calendar JS: Erro na resposta (Não JSON ou falha no parse):", response.statusText, jsonError);
                     throw new Error(`Erro ${response.status}: ${response.statusText || 'Erro desconhecido'}`);
                });
            }
            return response.json();
        })
        .then(result => {
            console.log('Admin Calendar JS: Sucesso AJAX:', result);
            if (result.status === 'success') {
                // --- INÍCIO DA MODIFICAÇÃO ---
                // Remove o alert
                // alert(result.message || 'Ação realizada com sucesso!');
                // Mantém o reload para que a mensagem do Django seja exibida
                location.reload();
                // --- FIM DA MODIFICAÇÃO ---
            } else {
                alert('Erro: ' + (result.message || 'Ocorreu um problema no servidor.'));
                buttonElement.disabled = false;
                if (buttonElement.classList.contains('confirm-scale-btn')) buttonElement.textContent = 'Confirmar Selecionado';
                else if (buttonElement.classList.contains('add-scale-btn')) buttonElement.textContent = 'Adicionar Selecionado';
            }
        })
        .catch(error => {
            console.error('Admin Calendar JS: Erro no Fetch ou processamento:', error);
            alert('Erro ao conectar com o servidor: ' + error.message);
            buttonElement.disabled = false;
            if (buttonElement.classList.contains('confirm-scale-btn')) buttonElement.textContent = 'Confirmar Selecionado';
            else if (buttonElement.classList.contains('add-scale-btn')) buttonElement.textContent = 'Adicionar Selecionado';
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

});
