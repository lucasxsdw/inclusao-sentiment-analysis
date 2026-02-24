document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const inputMensagem = document.getElementById("mensagem-input");
    const btnEnviar = document.getElementById("btn-enviar");

    // 1. Enviar ao clicar no botão
    btnEnviar.addEventListener("click", enviarMensagem);

    // 2. Enviar ao apertar "Enter" (sem Shift, para permitir quebra de linha)
    inputMensagem.addEventListener("keydown", function(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault(); // Impede de pular linha
            enviarMensagem();
        }
    });

    // 3. Função que aumenta o tamanho do campo de texto conforme o aluno digita
    inputMensagem.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight) + "px";
        if(this.value === "") this.style.height = "auto";
    });

    // --- FUNÇÃO PRINCIPAL DE ENVIO ---
    async function enviarMensagem() {
        const textoAluno = inputMensagem.value.trim();
        if (textoAluno === "") return;

        // Limpa o campo e foca nele de novo
        inputMensagem.value = "";
        inputMensagem.style.height = "auto";

        // Adiciona a mensagem do aluno na tela
        adicionarMensagemUsuario(textoAluno);

        // Adiciona o balãozinho de "A IA está digitando..."
        const idLoading = mostrarLoadingBot();

        try {
            // Pegamos o token de segurança do Django
            const csrftoken = getCookie('csrftoken');

            // Conecta com o Backend (A nossa view enviar_desabafo)
            const resposta = await fetch('/analise/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken // Mostramos o "crachá" para o Django liberar o POST
                },
                body: JSON.stringify({ texto_resposta: textoAluno })
            });

            const dados = await resposta.json();
            
            // Remove o balãozinho de "digitando..."
            removerLoadingBot(idLoading);

            if (resposta.ok) {
                // Sucesso! A IA respondeu.
                adicionarMensagemBot(dados.resposta_assistente);
            } else {
                adicionarMensagemBot("Poxa, estou com um probleminha de conexão agora. Tente me mandar de novo!");
                console.error("Erro da API:", dados.erro);
            }

        } catch (erro) {
            removerLoadingBot(idLoading);
            adicionarMensagemBot("Erro de conexão. Verifique se o servidor está rodando e sua internet.");
            console.error("Falha no Fetch:", erro);
        }
    }

    // --- FUNÇÕES DE RENDERIZAÇÃO NA TELA ---
    function adicionarMensagemUsuario(texto) {
        const div = document.createElement("div");
        div.className = "user-message";
        div.innerHTML = `<span>${escaparHTML(texto)}</span>`;
        chatBox.appendChild(div);
        rolarParaFinal();
    }

    function adicionarMensagemBot(texto) {
        const div = document.createElement("div");
        div.className = "bot-message";
        div.innerHTML = `
            <div class="bot-icon" aria-hidden="true">🤖</div>
            <div class="bot-bubble">${escaparHTML(texto)}</div>
        `;
        chatBox.appendChild(div);
        rolarParaFinal();
    }

    function mostrarLoadingBot() {
        const idAleatorio = 'loading-' + Math.random().toString(36).substr(2, 9);
        const div = document.createElement("div");
        div.className = "bot-message";
        div.id = idAleatorio;
        div.innerHTML = `
            <div class="bot-icon" aria-hidden="true">🤖</div>
            <div class="bot-bubble typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatBox.appendChild(div);
        rolarParaFinal();
        return idAleatorio;
    }

    function removerLoadingBot(id) {
        const elemento = document.getElementById(id);
        if (elemento) elemento.remove();
    }

    function rolarParaFinal() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- FUNÇÕES DE SEGURANÇA E AUXILIARES ---

    // Prevenção de Segurança (XSS - Impede que injetem código HTML no chat)
    function escaparHTML(texto) {
        return texto
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Função oficial do Django para ler o Token CSRF salvo nos cookies do navegador
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