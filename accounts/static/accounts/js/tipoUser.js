// acessibilidade + seleção visual
const options = document.querySelectorAll('.option');

options.forEach(option => {
    option.addEventListener('click', () => {
        options.forEach(o => o.classList.remove('selected'));
        option.classList.add('selected');
        option.querySelector('input').checked = true;
    });

    option.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            option.click();
        }
    });
});