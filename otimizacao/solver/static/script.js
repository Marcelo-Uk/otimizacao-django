// solver/static/script.js

// Adiciona uma nova restrição
function addConstraint() {
    const div = document.createElement('div');
    div.className = 'constraint';
    div.innerHTML = `
        <input type="text" placeholder="Exemplo: x1+x2<=10" class="con-restriction">
        <button onclick="removeConstraint(this)">Remover</button>
    `;
    document.getElementById('constraints').appendChild(div);
}

// Remove uma restrição
function removeConstraint(button) {
    button.parentElement.remove();
}

// Obtém o token CSRF
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length, cookie.length);
        }
    }
    return null;
}

// Envia os dados para otimização
async function fetchResults() {
    const objective = document.getElementById('objectiveType').value;
    const objectiveFunction = document.getElementById('objectiveFunction').value;

    const constraints = Array.from(document.querySelectorAll('.con-restriction'))
        .map(el => el.value);

    const nonNegativity = {
        x1: document.getElementById('nonNegativityX1').checked,
        x2: document.getElementById('nonNegativityX2').checked
    };

    const data = {
        objective,
        objectiveFunction,
        constraints,
        nonNegativity
    };

    try {
        const csrfToken = getCSRFToken();
        const response = await fetch('/solver/optimize/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        document.getElementById('result').innerHTML =
        `<div><strong>Ponto Ótimo:</strong> ${result['Ponto Ótimo']}</div><div><strong>Resultado Objetivo:</strong> ${result['Resultado Objetivo']}</div>
    `;

        document.getElementById('restrictionPoints').innerHTML = result['Pontos Restrição']
            .map(r => `${r['Restrição']}: (${r['Pontos'][0][0]}, ${r['Pontos'][0][1]}) → (${r['Pontos'][1][0]}, ${r['Pontos'][1][1]})`)
            .join('<br>');

        document.getElementById('graph-image').src = result['graph_path'] + '?t=' + new Date().getTime();
        document.getElementById('graphSection').style.display = 'block';
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro inesperado.');
    }
}
