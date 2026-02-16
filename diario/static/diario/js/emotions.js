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

      const csrfTokenElement = document.querySelector(
        'meta[name="csrf-token"]'
      );
      const csrfToken = csrfTokenElement
        ? csrfTokenElement.content
        : "";

      fetch("/diario/salvar-emocao/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({
          emocao: emocaoSelecionada
        })
      })
        .then(response => response.json())
        .then(data => {
          if (data.status === "ok") {
            window.location.href = "/proxima-pagina/";
          } else {
            alert("Erro ao salvar emoção.");
          }
        })
        .catch(error => {
          console.error("Erro:", error);
        });
    });
  }
});
