import matplotlib
matplotlib.use('Agg')  # Backend adequado para renderizar gráficos em servidores

from django.shortcuts import render
from django.http import JsonResponse
from pulp import LpProblem, LpVariable, LpMaximize, LpMinimize, lpSum, value
import os
import json
import re
import numpy as np
import matplotlib.pyplot as plt

############### Controle de Versão: FINAL #1 ###############

# View inicial
def index(request):
    return render(request, 'index.html')

# View para geração de gráficos
def graph(request):
    filepath = 'solver/static/graph.png'
    if os.path.exists(filepath):
        return FileResponse(open(filepath, 'rb'), content_type='image/png')
    else:
        return JsonResponse({'error': 'Gráfico não encontrado. Gere um gráfico primeiro.'}, status=404)


# Função para parsear expressões matemáticas
def parse_expression(expression, variables):
    try:
        terms = re.findall(r'([+-]?\s*\d*\.*\d*)\s*([a-zA-Z_][a-zA-Z0-9_]*)', expression)
        parsed_terms = []
        for coef, var in terms:
            coef = coef.replace(' ', '')  # Remove espaços
            if coef in ('', '+'):
                coef = 1
            elif coef == '-':
                coef = -1
            else:
                coef = float(coef)

            if var not in variables:
                variables[var] = LpVariable(var, lowBound=0)

            parsed_terms.append(coef * variables[var])
        return lpSum(parsed_terms)
    except Exception as e:
        raise ValueError(f"Erro ao analisar a expressão: {expression}. Detalhes: {str(e)}")


# Função para calcular dois pontos de uma reta
def find_line_points(lhs: str, rhs: float):
    """
    Encontra dois pontos para uma restrição:
    - Ponto A (0, ?)
    - Ponto B (?, 0)
    """
    try:
        lhs = lhs.replace(' ', '').replace('--', '+').replace('+-', '-')
        x1_coef = re.search(r'([+-]?\d*)x1', lhs)
        x2_coef = re.search(r'([+-]?\d*)x2', lhs)

        x1_coef = float(x1_coef.group(1)) if x1_coef and x1_coef.group(1) not in ('', '+', '-') else (-1 if x1_coef and x1_coef.group(1) == '-' else 1)
        x2_coef = float(x2_coef.group(1)) if x2_coef and x2_coef.group(1) not in ('', '+', '-') else (-1 if x2_coef and x2_coef.group(1) == '-' else 1)

        # Calcular pontos A (0, y) e B (x, 0)
        y_intercept = rhs / x2_coef if x2_coef != 0 else 0
        x_intercept = rhs / x1_coef if x1_coef != 0 else 0

        return (0, y_intercept), (x_intercept, 0)
    except Exception as e:
        print(f"Erro ao calcular pontos da restrição: {e}")
        return (0, 0), (0, 0)


# Função principal de otimização
def optimize(request):
    if request.method == 'POST':
        try:
            # Obter dados do POST
            data = json.loads(request.body)
            objective = data['objective']
            objectiveFunction = data['objectiveFunction']
            constraints = data['constraints']
            non_negativity = data.get('nonNegativity', {'x1': True, 'x2': True})

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

            # Adicionar restrições de não negatividade
            if non_negativity.get('x1', True):
                model += variables['x1'] >= 0
            if non_negativity.get('x2', True):
                model += variables['x2'] >= 0

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

            # Desenhar eixos principais
            plt.axhline(0, color='black', linewidth=2)  # Eixo X
            plt.axvline(0, color='black', linewidth=2)  # Eixo Y

            # Intervalo amplo para melhor visualização
            x_range = np.linspace(-1, 10, 400)

            for i, (lhs, operator, rhs) in enumerate(constraint_lines):
                try:
                    # Processar a expressão para obter coeficientes
                    lhs = lhs.replace(' ', '').replace('--', '+').replace('+-', '-')
                    lhs = re.sub(r'(?<![\d.])x', '1x', lhs)  # Substitui 'x' por '1x' se não houver número antes
                    lhs = re.sub(r'(?<![\d.])-x', '-1x', lhs)  # Substitui '-x' por '-1x' se não houver número antes
                    lhs = re.sub(r'(?<![\d.])\+x', '+1x', lhs)  # Substitui '+x' por '+1x' se não houver número antes
                    
                    coef_match = re.match(r'([+-]?\d*\.?\d*)x1([+-]?\d*\.?\d*)x2', lhs)
                    
                    if coef_match:
                        coef_x1 = float(coef_match.group(1)) if coef_match.group(1) else 1
                        coef_x2 = float(coef_match.group(2)) if coef_match.group(2) else 1

                        # Calcular valores de y para toda a extensão do eixo x
                        y_range = (rhs - coef_x1 * x_range) / coef_x2

                        # Desenhar a reta
                        plt.plot(x_range, y_range, label=f'Restrição {i + 1}', linewidth=2)

                        # Preencher a região factível apenas em regiões positivas
                        if operator == '<=':
                            plt.fill_between(
                                x_range,
                                y_range,
                                -100,
                                alpha=0.2,
                                color='gray',
                                where=(x_range >= 0) if non_negativity['x1'] else True
                            )
                        elif operator == '>=':
                            plt.fill_between(
                                x_range,
                                y_range,
                                100,
                                alpha=0.2,
                                color='gray',
                                where=(x_range >= 0) if non_negativity['x1'] else True
                            )

                except ZeroDivisionError:
                    print(f"Erro: Divisão por zero ao desenhar restrição {i + 1}")
                except Exception as e:
                    print(f"Erro ao desenhar restrição {i + 1}: {e}")

            # Adicionar ponto ótimo ao gráfico com anotação
            plt.scatter(optimal_point[0], optimal_point[1], color='red', s=100, label='Solução Ótima')
            plt.text(optimal_point[0], optimal_point[1], f'({optimal_point[0]}, {optimal_point[1]})', fontsize=10, color='red')

            # Ajustar limites positivos
            plt.xlim(0 if non_negativity['x1'] else -1, 10)
            plt.ylim(0 if non_negativity['x2'] else -1, 10)

            # Adicionar grid
            plt.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)

            # Adicionar legenda
            plt.legend()

            # Salvar gráfico
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
