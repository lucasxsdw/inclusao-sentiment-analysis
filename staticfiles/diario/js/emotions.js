document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll(".emotion-btn");
  const continuar = document.querySelector(".continuar-btn");

  let emocaoSelecionada = null;

  // 🔹 Seleção da emoção
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      document
        .querySelector(".emotion-btn.selected")
        ?.classList.remove("selected");

      btn.classList.add("selected");
      emocaoSelecionada = btn.dataset.emotion;

      console.log("Emoção selecionada:", emocaoSelecionada);

      if (continuar) {
        continuar.disabled = false;
        continuar.setAttribute("aria-disabled", "false");
      }
    });
  });

  // 🔹 Envio para o backend
  
  if (continuar) {
    continuar.addEventListener("click", () => {
      if (!emocaoSelecionada) return;

      // Função para pegar o token direto do cookie do navegador
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

      const csrfToken = getCookie('csrftoken'); // Agora ele pega o token real

      fetch("/diario/salvar_emocao/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken // Envia o selo de segurança
        },
        body: JSON.stringify({
          emocao: emocaoSelecionada
        })
      })
      .then(response => {
        if (!response.ok) {
           // Se der erro 403 ou 500, vamos ver o texto do erro no console
           return response.text().then(text => { throw new Error(text) });
        }
        return response.json();
      })
      .then(data => {
        if (data.status === "success") {
          window.location.href = "/analise/chat/";
        } else {
          alert("Erro: " + (data.message || "Erro ao salvar"));
        }
      })
      .catch(error => {
        console.error("Erro detalhado:", error);
      });
    });
  }
});

