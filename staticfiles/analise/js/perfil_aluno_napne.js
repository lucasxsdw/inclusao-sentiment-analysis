document.addEventListener("DOMContentLoaded", function () {
    const canvas = document.getElementById('meuGrafico');

    if (canvas) {
        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'line', 
            data: {
                // Aqui é a mágica! Buscamos os dados do HTML
                labels: window.dadosDoGrafico.datas, 
                datasets: [{
                    label: 'Nível de Bem-estar',
                    data: window.dadosDoGrafico.scores, 
                    borderColor: '#10b981', 
                    backgroundColor: 'rgba(16, 185, 129, 0.2)', 
                    tension: 0.3, 
                    fill: true 
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100 
                    }
                }
            }
        });
    }


   
});