document.addEventListener("DOMContentLoaded", function() {
    // Seleciona a lista inteira
    const checklist = document.querySelector('.checklist');
    
    // ACESSIBILIDADE: Verifica se o usuário ativou a preferência de reduzir movimentos no sistema operacional (Windows/Mac/Android/iOS)
    const prefereMenosMovimento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    // Configura o observador para detectar quando a lista aparece na tela
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Pega todos os itens (li) dentro da lista
                const items = entry.target.querySelectorAll('.check-item');
                
                // Adiciona a classe 'show'
                items.forEach((item, index) => {
                    if (prefereMenosMovimento) {
                        // Se for PCD/com vertigem, mostra tudo instantaneamente sem o atraso
                        item.classList.add('show');
                    } else {
                        // Se não, usa o seu efeito em cascata (stagger effect)
                        setTimeout(() => {
                            item.classList.add('show');
                        }, index * 150); // 150ms de intervalo
                    }
                });
                
                // Para de observar depois que a animação rodar a primeira vez
                observer.unobserve(entry.target);
            }
        });
    }, { 
        threshold: 0.2 // A animação começa quando 20% da lista estiver visível
    });

    // Inicia a observação
    if (checklist) {
        observer.observe(checklist);
    }
});