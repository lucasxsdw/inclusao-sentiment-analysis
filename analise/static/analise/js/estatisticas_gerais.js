document.addEventListener("DOMContentLoaded", function () {

        // 1. Puxa os dados gerados com segurança pelo Django no HTML
        const labelsElement=document.getElementById('labelsData');
        const dataElement=document.getElementById('valoresData');

        // Se não encontrar os dados (evita erro se a página carregar vazia)
        if ( !labelsElement || !dataElement) return;

        const labels=JSON.parse(labelsElement.textContent);
        const data=JSON.parse(dataElement.textContent);

        const canvas=document.getElementById('graficoDistribuicao');
        if ( !canvas) return;

        const ctx=canvas.getContext('2d');

        // 2. Monta o Gráfico
        new Chart(ctx, {

            type: 'doughnut',
            data: {

                labels: labels,
                datasets: [ {
                    data: data,
                    backgroundColor: [ '#10b981', // Verde
                    '#0ea5e9', // Azul
                    '#6366f1', // Indigo
                    '#f59e0b', // Laranja
                    '#ef4444', // Vermelho
                    '#8b5cf6', // Roxo
                    '#14b8a6', // Teal
                    '#f43f5e' // Rosa
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }

                ]
            }

            ,
            options: {

                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {

                        position: 'right',
                        labels: {
                            padding: 20, font: {
                                family: 'Inter'
                            }
                        }
                    }
                }

                ,
                cutout: '65%'
            }
        });
});