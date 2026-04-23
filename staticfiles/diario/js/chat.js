 document.addEventListener("DOMContentLoaded", function () {

    const btnEnviar = document.getElementById("btn-enviar");
    const chatBox = document.getElementById("chat-box");
    const mensagemInput = document.getElementById("mensagem");

    function adicionarMensagem(texto, tipo) {
        const div = document.createElement("div");
        div.classList.add("message", tipo);
        div.innerText = texto;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    btnEnviar.addEventListener("click", function () {

        const texto = mensagemInput.value.trim();
        if (!texto) return;

        adicionarMensagem(texto, "user");
        mensagemInput.value = "";

        fetch("/salvar-resposta/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({
                diario_id: DIARIO_ID,
                pergunta_id: PERGUNTA_ID,
                texto: texto
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                adicionarMensagem(
                    "Percebo que você está sentindo " + data.sentimento_detectado,
                    "ia"
                );
            }
        });
    });

    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
               document.cookie.split('; ')
               .find(row => row.startsWith('csrftoken'))
               ?.split('=')[1];
    }

});
