from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from pulp import LpProblem, LpVariable, LpMaximize, LpMinimize, lpSum
import matplotlib.pyplot as plt
import os
import json
import re
from django.middleware.csrf import get_token
from pulp import value

# View para renderizar a página inicial
def index(request):
    csrf_token = get_token(request)
    return render(request, 'index.html', {'csrf_token': csrf_token})

# Função auxiliar para parsear expressões
def parse_expression(expression, variables):
    try:
        terms = re.findall(r'([+-]?\s*\d*\.*\d*)\s*([a-zA-Z_][a-zA-Z0-9_]*)', expression)
        parsed_terms = []
        for coef, var in terms:
            coef = coef.replace(' ', '')  # Remove espaços
            if coef in ('', '+'):  # Coeficiente implícito positivo
                coef = 1
            elif coef == '-':  # Coeficiente implícito negativo
                coef = -1
            else:
                coef = float(coef)

            if var not in variables:
                variables[var] = LpVariable(var, lowBound=0)

            parsed_terms.append(coef * variables[var])
        return lpSum(parsed_terms)
    except Exception as e:
        raise ValueError(f"Erro ao analisar a expressão: {expression}. Detalhes: {str(e)}")


# Função principal de otimização
def optimize(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            objective = data['objective']
            objectiveFunction = data['objectiveFunction']
            constraints = data['constraints']

            # Criar o modelo
            sense = LpMaximize if objective == 'maximize' else LpMinimize
            model = LpProblem('Optimization', sense)

            # Definir variáveis automaticamente
            variables = {}

            # Função objetivo
            model += parse_expression(objectiveFunction, variables), 'Objective'

            # Restrições
            for c in constraints:
                match = re.match(r'(.+?)(<=|>=|=)(.+)', c.replace(' ', ''))
                if match:
                    lhs = parse_expression(match.group(1), variables)
                    operator = match.group(2)
                    rhs = float(match.group(3))
                    if operator == '<=':
                        model += lhs <= rhs
                    elif operator == '>=':
                        model += lhs >= rhs
                    elif operator == '=':
                        model += lhs == rhs
                else:
                    return JsonResponse({'error': f'Restrição inválida: {c}'}, status=400)

            model.solve()

            # Capturar resultados
            optimal_point = [v.varValue for v in model.variables()]
            objective_result = value(model.objective)

            # Geração do gráfico
            filepath = 'solver/static/graph.png'
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            plt.figure(figsize=(8, 6))
            plt.xlabel('x1')
            plt.ylabel('x2')

            # Plotar espaço factível e ponto ótimo
            x = range(0, 10)
            y = [4 - xi for xi in x]  # Exemplo simplificado de restrição
            plt.plot(x, y, label='Restrição 1')
            plt.fill_between(x, 0, y, color='skyblue', alpha=0.3)
            plt.scatter(optimal_point[0], optimal_point[1], color='red', label='Solução Ótima')
            plt.legend()
            plt.savefig(filepath)
            plt.close()

            return JsonResponse({
                'Ponto Ótimo': f"({', '.join(map(str, optimal_point))})",
                'Resultado Objetivo': objective_result,
                'graph_path': f"/static/graph.png"
            })

        except ValueError as ve:
            return JsonResponse({'error': str(ve)}, status=400)
        except Exception as e:
            return JsonResponse({'error': f"Erro inesperado: {str(e)}"}, status=500)


# View para geração de gráficos
def graph(request):
    plt.figure()
    plt.plot([0, 5], [5, 0], label='Restrição 1')
    plt.fill_between([0, 5], [5, 0], color='skyblue', alpha=0.3)
    plt.scatter([2], [3], color='red', label='Solução Ótima')
    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.legend()
    filepath = 'solver/static/graph.png'
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    plt.savefig(filepath)
    return FileResponse(open(filepath, 'rb'), content_type='image/png')
