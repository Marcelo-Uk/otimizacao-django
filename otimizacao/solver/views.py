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
import sympy as sp


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


# Função para calcular pontos de interseção entre duas restrições
def calculate_intersection(lhs1, rhs1, lhs2, rhs2):
    try:
        x1, x2 = sp.symbols('x1 x2')
        eq1 = sp.parse_expr(lhs1, local_dict={'x1': x1, 'x2': x2}) - rhs1
        eq2 = sp.parse_expr(lhs2, local_dict={'x1': x1, 'x2': x2}) - rhs2
        solution = sp.solve((eq1, eq2), (x1, x2))
        return (float(solution[x1]), float(solution[x2]))
    except Exception as e:
        print(f"Erro ao calcular interseção: {e}")
        return None


# Função para encontrar pontos de uma reta
def find_line_points(lhs, rhs):
    """
    Encontra dois pontos para uma restrição:
    - Ponto A (0, ?)
    - Ponto B (?, 0)
    """
    try:
        # Garantir que a expressão está formatada corretamente
        lhs = lhs.replace(' ', '').replace('--', '+').replace('+-', '-')

        # Coeficientes para x1 e x2
        coef_x1 = 0
        coef_x2 = 0
        terms = re.findall(r'([+-]?\d*\.?\d*)\*?(x1|x2)', lhs)

        for coef, var in terms:
            coef = float(coef) if coef not in ('', '+', '-') else float(coef + '1')
            if var == 'x1':
                coef_x1 = coef
            elif var == 'x2':
                coef_x2 = coef

        # Resolver para x2 quando x1 = 0
        y_value = rhs / coef_x2 if coef_x2 != 0 else 0

        # Resolver para x1 quando x2 = 0
        x_value = rhs / coef_x1 if coef_x1 != 0 else 0

        return (0, y_value), (x_value, 0)
    except ZeroDivisionError:
        print("Erro: Divisão por zero ao calcular os pontos da reta.")
        return (0, 0), (0, 0)
    except Exception as e:
        print(f"Erro ao calcular pontos da restrição: {e}")
        return (0, 0), (0, 0)

# Função principal de otimização (MATPLOTLIB)
def optimize(request):
    if request.method == 'POST':
        try:
            # Obter dados do POST
            data = json.loads(request.body)
            objective = data['objective']
            objectiveFunction = data['objectiveFunction']
            constraints = data['constraints']

            # Criar modelo de otimização
            sense = LpMaximize if objective == 'maximize' else LpMinimize
            model = LpProblem('Optimization', sense)

            # Definir variáveis automaticamente
            variables = {}
            restriction_points = []
            constraint_lines = []

            # Adicionar função objetivo
            model += parse_expression(objectiveFunction, variables), 'Objective'

            # Adicionar restrições
            for i, c in enumerate(constraints):
                match = re.match(r'(.+?)(<=|>=|=)(.+)', c.replace(' ', ''))
                if match:
                    lhs = match.group(1)
                    operator = match.group(2)
                    rhs = float(match.group(3))
                    
                    constraint_lines.append((lhs, operator, rhs))

                    if operator == '<=':
                        model += parse_expression(lhs, variables) <= rhs
                    elif operator == '>=':
                        model += parse_expression(lhs, variables) >= rhs
                    elif operator == '=':
                        model += parse_expression(lhs, variables) == rhs

                    # Calcular pontos para o gráfico
                    A, B = find_line_points(lhs, rhs)
                    restriction_points.append({
                        'Restrição': f'Restrição {i + 1}',
                        'Pontos': [A, B]
                    })

            # Resolver o modelo
            model.solve()
            optimal_point = [v.varValue for v in model.variables()]
            objective_result = value(model.objective)

            # Gerar gráfico com Matplotlib
            filepath = 'solver/static/graph.png'
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            plt.figure(figsize=(10, 8))
            plt.xlabel('x1')
            plt.ylabel('x2')
            plt.title('Gráfico da Região Factível e Solução Ótima')

            # Desenhar eixos principais em preto e mais grossos
            plt.axhline(0, color='black', linewidth=2)  # Eixo X
            plt.axvline(0, color='black', linewidth=2)  # Eixo Y

            # Intervalo amplo para melhor visualização
            x_range = np.linspace(-10, 10, 400)

            for i, (lhs, operator, rhs) in enumerate(constraint_lines):
                try:
                    # Processar a expressão para obter coeficientes
                    lhs = lhs.replace(' ', '').replace('--', '+').replace('+-', '-')
                    coef_match = re.match(r'([+-]?\d*\.?\d*)x1([+-]?\d*\.?\d*)x2', lhs)
                    
                    if coef_match:
                        coef_x1 = coef_match.group(1)
                        coef_x2 = coef_match.group(2)

                        # Ajustar coeficientes para valores padrão se estiverem vazios
                        coef_x1 = float(coef_x1) if coef_x1 and coef_x1 != '-' else -1 if coef_x1 == '-' else 1
                        coef_x2 = float(coef_x2) if coef_x2 and coef_x2 != '-' else -1 if coef_x2 == '-' else 1

                        # Calcular valores de y para toda a extensão do eixo x
                        y_range = (rhs - coef_x1 * x_range) / coef_x2

                        # Desenhar a reta
                        plt.plot(x_range, y_range, label=f'Restrição {i + 1}')

                        # Preencher a região factível
                        if operator == '<=':
                            plt.fill_between(x_range, y_range, -100, alpha=0.2, label=f'Região Restrição {i + 1}')
                        elif operator == '>=':
                            plt.fill_between(x_range, y_range, 100, alpha=0.2, label=f'Região Restrição {i + 1}')

                except ZeroDivisionError:
                    print(f"Erro: Divisão por zero ao desenhar restrição {i + 1}")
                except Exception as e:
                    print(f"Erro ao desenhar restrição {i + 1}: {e}")

            # Adicionar ponto ótimo ao gráfico
            plt.scatter(optimal_point[0], optimal_point[1], color='red', s=100, label='Solução Ótima')

            # Ajustar limites do gráfico
            plt.xlim(-10, 10)
            plt.ylim(-10, 10)
            plt.legend()
            plt.grid(True)
            plt.savefig(filepath)
            plt.close()

            return JsonResponse({
                'Ponto Ótimo': f"({', '.join(map(str, optimal_point))})",
                'Resultado Objetivo': objective_result,
                'Pontos Restrição': restriction_points,
                'graph_path': f"/static/graph.png"
            })

        except ValueError as ve:
            return JsonResponse({'error': str(ve)}, status=400)
        except ZeroDivisionError:
            return JsonResponse({'error': 'Erro: Divisão por zero ao calcular pontos de restrição.'}, status=400)
        except Exception as e:
            print(f"Erro inesperado: {e}")
            return JsonResponse({'error': f"Erro inesperado: {str(e)}"}, status=500)


# View para geração de gráficos
def graph(request):
    filepath = 'solver/static/graph.png'
    if os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), content_type='image/png')
    else:
        return JsonResponse({'error': 'Gráfico não encontrado. Gere um gráfico primeiro.'}, status=404)
