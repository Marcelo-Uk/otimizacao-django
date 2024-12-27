import matplotlib
matplotlib.use('Agg')  # Backend adequado para renderizar gráficos em servidores

from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from pulp import LpProblem, LpVariable, LpMaximize, LpMinimize, lpSum
import matplotlib.pyplot as plt
import os
import json
import re
from django.middleware.csrf import get_token
from pulp import value
import numpy as np

import plotly.graph_objects as go
import plotly.io as pio

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


# Função principal de otimização (MATPLOTLIB)
#def optimize(request):
#    if request.method == 'POST':
#        try:
#            data = json.loads(request.body)
#            objective = data['objective']
#            objectiveFunction = data['objectiveFunction']
#            constraints = data['constraints']
#
#            # Criar o modelo
#            sense = LpMaximize if objective == 'maximize' else LpMinimize
#            model = LpProblem('Optimization', sense)
#
#            # Definir variáveis automaticamente
#            variables = {}
#
#            # Função objetivo
#            model += parse_expression(objectiveFunction, variables), 'Objective'
#
#            # Armazenar as restrições para o gráfico
#            constraint_lines = []
#
#            for c in constraints:
#                match = re.match(r'(.+?)(<=|>=|=)(.+)', c.replace(' ', ''))
#                if match:
#                    lhs = parse_expression(match.group(1), variables)
#                    operator = match.group(2)
#                    rhs = float(match.group(3))
#                    constraint_lines.append((match.group(1), operator, rhs))  # Salva para o gráfico
#
#                    if operator == '<=':
#                        model += lhs <= rhs
#                    elif operator == '>=':
#                        model += lhs >= rhs
#                    elif operator == '=':
#                        model += lhs == rhs
#                else:
#                    return JsonResponse({'error': f'Restrição inválida: {c}'}, status=400)
#
#            model.solve()
#
#            # Capturar resultados
#            optimal_point = [v.varValue for v in model.variables()]
#            objective_result = value(model.objective)
#
#            # Determinar os limites do eixo X dinamicamente
#            x_min = min(optimal_point[0], 0) - 2  # Garantir uma margem
#            x_max = max(optimal_point[0], 0) + 2
#
#            filepath = 'solver/static/graph.png'
#            os.makedirs(os.path.dirname(filepath), exist_ok=True)
#
#            plt.figure(figsize=(8, 6))
#            plt.xlabel('x1')
#            plt.ylabel('x2')
#
#            x = np.linspace(x_min, x_max, 200)  # Mais pontos para maior precisão
#
#            for i, (lhs, operator, rhs) in enumerate(constraint_lines):
#                try:
#                    # Garantir que lhs está formatado corretamente
#                    lhs = lhs.replace('x1', '*x').replace('x2', '*y').replace('--', '+').replace('+-', '-')
#
#                    if '*x' in lhs and '*y' in lhs:
#                        # Restrição com x1 e x2
#                        def y_func(x_val):
#                            return (rhs - eval(lhs.replace('*x', str(x_val)).replace('*y', '0'))) / eval(
#                                lhs.replace('*x', '0').replace('*y', '1')
#                            )
#
#                        y_vals = []
#                        for val in x:
#                            try:
#                                y_vals.append(y_func(val))
#                            except ZeroDivisionError:
#                                y_vals.append(float('inf'))
#
#                        plt.plot(x, y_vals, label=f'Restrição {i + 1}')
#                        if operator == '<=':
#                            plt.fill_between(x, -100, y_vals, color='skyblue', alpha=0.3)
#                        elif operator == '>=':
#                            plt.fill_between(x, y_vals, 100, color='lightcoral', alpha=0.3)
#
#                    elif '*x' in lhs and '*y' not in lhs:
#                        # Restrição dependente apenas de x1 (reta vertical)
#                        x_val = rhs / eval(lhs.replace('*x', '1'))
#                        plt.axvline(x=x_val, color='green', linestyle='--', label=f'Restrição {i + 1}')
#
#                    elif '*y' in lhs and '*x' not in lhs:
#                        # Restrição dependente apenas de x2 (reta horizontal)
#                        y_val = rhs / eval(lhs.replace('*y', '1'))
#                        plt.axhline(y=y_val, color='purple', linestyle='--', label=f'Restrição {i + 1}')
#                except Exception as e:
#                    print(f"Erro ao desenhar restrição {i + 1}: {e}")
#
#            # Ajustar limites do gráfico
#            plt.xlim(x_min, x_max)
#            plt.ylim(0, max(optimal_point[1] + 2, 10))  # Ajuste do eixo Y com margem
#
#            # Marcar ponto ótimo
#            plt.scatter(optimal_point[0], optimal_point[1], color='red', label='Solução Ótima')
#            plt.legend()
#            plt.savefig(filepath)
#            plt.close()
#
#            return JsonResponse({
#                'Ponto Ótimo': f"({', '.join(map(str, optimal_point))})",
#                'Resultado Objetivo': objective_result,
#                'graph_path': f"/static/graph.png"
#            })
#
#        except ValueError as ve:
#            return JsonResponse({'error': str(ve)}, status=400)
#        except Exception as e:
#            return JsonResponse({'error': f"Erro inesperado: {str(e)}"}, status=500)
#

# Função principal de otimização (PLOTLY)
def optimize(request):
    if request.method == 'POST':
        try:
            import json
            from pulp import LpProblem, LpVariable, LpMaximize, LpMinimize, lpSum, value

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

            # Armazenar as restrições para o gráfico
            constraint_lines = []
            restriction_points = []

            for c in constraints:
                match = re.match(r'(.+?)(<=|>=|=)(.+)', c.replace(' ', ''))
                if match:
                    lhs = parse_expression(match.group(1), variables)
                    operator = match.group(2)
                    rhs = float(match.group(3))
                    constraint_lines.append((match.group(1), operator, rhs))

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

            # Determinar intervalo
            x_min = min(optimal_point[0], 0) - 2
            x_max = max(optimal_point[0], 0) + 2
            x = np.linspace(x_min, x_max, 200)

            # Gráfico com Plotly
            fig = go.Figure()

            for i, (lhs, operator, rhs) in enumerate(constraint_lines):
                try:
                    lhs = lhs.replace('x1', '*x').replace('x2', '*y').replace('--', '+').replace('+-', '-')
                    if '*x' in lhs and '*y' in lhs:
                        def y_func(x_val):
                            return (rhs - eval(lhs.replace('*x', str(x_val)).replace('*y', '0'))) / eval(
                                lhs.replace('*x', '0').replace('*y', '1')
                            )

                        y_vals = [y_func(val) for val in x]
                        fig.add_trace(go.Scatter(
                            x=x, 
                            y=y_vals, 
                            mode='lines',
                            name=f'Restrição {i+1}'
                        ))

                        restriction_points.append({
                            'Restrição': f'Restrição {i + 1}',
                            'Pontos': [(x[0], y_vals[0]), (x[-1], y_vals[-1])]
                        })
                except Exception as e:
                    print(f"Erro ao desenhar restrição {i + 1}: {e}")

            # Adicionar ponto ótimo
            fig.add_trace(go.Scatter(
                x=[optimal_point[0]],
                y=[optimal_point[1]],
                mode='markers',
                marker=dict(color='red', size=10),
                name='Solução Ótima'
            ))

            fig.update_layout(
                title="Gráfico de Otimização",
                xaxis_title="x1",
                yaxis_title="x2",
                legend=dict(x=0, y=1)
            )

            # Salvar gráfico como HTML na pasta static
            static_dir = os.path.join(os.path.dirname(__file__), 'static')
            os.makedirs(static_dir, exist_ok=True)

            graph_path = os.path.join(static_dir, 'graph.html')
            pio.write_html(fig, file=graph_path, auto_open=False)

            return JsonResponse({
                'Ponto Ótimo': f"({', '.join(map(str, optimal_point))})",
                'Resultado Objetivo': objective_result,
                'Pontos Restrição': restriction_points,
                'graph_path': f"/static/graph.html"
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
