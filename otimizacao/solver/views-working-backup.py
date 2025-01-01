
#Essa views está rodando o sistema
#Porém, existe um erro quando a função objetivo é no formato: 10x1+30x2+4000

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

############### Controle de Versão: FINAL FULL ###############

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
    - Para equações com duas variáveis: Ponto A (0, ?) e Ponto B (?, 0)
    - Para equações com apenas x1: Ponto A (rhs, 0) e Ponto B (rhs, 2)
    - Para equações com apenas x2: Ponto A (0, rhs/coef) e Ponto B (2, rhs/coef)
    """
    try:
        lhs = lhs.replace(' ', '').replace('--', '+').replace('+-', '-')
        x1_match = re.search(r'([+-]?\d*\.?\d*)x1', lhs)
        x2_match = re.search(r'([+-]?\d*\.?\d*)x2', lhs)

        # Captura os coeficientes ou assume 1 quando omitidos
        x1_coef = float(x1_match.group(1)) if x1_match and x1_match.group(1) not in ('', '+', '-') else (-1 if x1_match and x1_match.group(1) == '-' else 1)
        x2_coef = float(x2_match.group(1)) if x2_match and x2_match.group(1) not in ('', '+', '-') else (-1 if x2_match and x2_match.group(1) == '-' else 1)

        # ⚠️ Resolução da Equação ⚠️
        # Caso com apenas x1 (ex: x1 <= 5)
        if x1_match and not x2_match:
            return (rhs / x1_coef, 0), (rhs / x1_coef, 2)

        # Caso com apenas x2 (ex: 2x2 <= 30)
        if x2_match and not x1_match:
            resolved_rhs = rhs / x2_coef  # Resolvendo a equação para x2
            return (0, resolved_rhs), (2, resolved_rhs)

        # Caso padrão com duas variáveis (ex: -x1 + 2x2 <= 4)
        y_intercept = rhs / x2_coef if x2_coef != 0 else 0
        x_intercept = rhs / x1_coef if x1_coef != 0 else 0

        return (0, y_intercept), (x_intercept, 0)

    except ZeroDivisionError:
        print("Erro: Divisão por zero ao calcular pontos de restrição.")
        return (0, 0), (0, 0)
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
            x_range = np.linspace(-1, 10000, 40000)
            y_range = np.linspace(-1, 10000, 40000)

            # Ponto coringa (0,0)
            coringa_x = 0
            coringa_y = 0

            for i, (lhs, operator, rhs) in enumerate(constraint_lines):
                try:
                    lhs = lhs.replace(' ', '').replace('--', '+').replace('+-', '-')
                    
                    # Substituir sinais sem números explícitos
                    lhs = re.sub(r'(?<![\d.])x', '1x', lhs)  # Substitui 'x' por '1x'
                    lhs = re.sub(r'(?<![\d.])-x', '-1x', lhs)  # Substitui '-x' por '-1x'
                    lhs = re.sub(r'(?<![\d.])\+x', '+1x', lhs)  # Substitui '+x' por '+1x'
            
                    # Coeficientes para x1 e x2 (extraídos do LHS)
                    x1_match = re.search(r'([+-]?\d*\.?\d*)x1', lhs)
                    x2_match = re.search(r'([+-]?\d*\.?\d*)x2', lhs)
            
                    x1_coef = float(x1_match.group(1)) if x1_match and x1_match.group(1) not in ('', '+', '-') else (-1 if x1_match and x1_match.group(1) == '-' else 1)
                    x2_coef = float(x2_match.group(1)) if x2_match and x2_match.group(1) not in ('', '+', '-') else (-1 if x2_match and x2_match.group(1) == '-' else 1)
            
                    # Tratamento para restrições verticais (ex: x1 <= 5)
                    if re.fullmatch(r'([+-]?\d*\.?\d*)x1', lhs) or re.fullmatch(r'x1', lhs):
                        if operator == '<=':
                            plt.axvline(x=rhs, color='purple', linewidth=2, label=f'Restrição {i + 1}')
                            plt.fill_betweenx(y_range, -100, rhs, alpha=0.2, color='gray')
                        elif operator == '>=':
                            plt.axvline(x=rhs, color='purple', linewidth=2, label=f'Restrição {i + 1}')
                            plt.fill_betweenx(y_range, rhs, 100, alpha=0.2, color='gray')
            
                    # Tratamento para restrições horizontais (ex: x2 <= 6)
                    elif re.fullmatch(r'([+-]?\d*\.?\d*)x2', lhs) or re.fullmatch(r'x2', lhs):
                        resolved_rhs = rhs / x2_coef if x2_coef != 0 else 0
                        if operator == '<=':
                            plt.axhline(y=resolved_rhs, color='green', linewidth=2, label=f'Restrição {i + 1}')
                            plt.fill_between(x_range, -100, resolved_rhs, alpha=0.2, color='gray')
                        elif operator == '>=':
                            plt.axhline(y=resolved_rhs, color='green', linewidth=2, label=f'Restrição {i + 1}')
                            plt.fill_between(x_range, resolved_rhs, 100, alpha=0.2, color='gray')
            
                    # Tratamento para restrições lineares
                    else:
                        coef_match = re.match(r'([+-]?\d*\.?\d*)x1([+-]?\d*\.?\d*)x2', lhs)
                        if coef_match:
                            coef_x1 = float(coef_match.group(1)) if coef_match.group(1) else 1
                            coef_x2 = float(coef_match.group(2)) if coef_match.group(2) else 1
            
                            y_values = (rhs - coef_x1 * x_range) / coef_x2
                            plt.plot(x_range, y_values, label=f'Restrição {i + 1}', linewidth=2)
            
                            if operator == '<=':
                                plt.fill_between(x_range, y_values, -100, alpha=0.2, color='gray')
                            elif operator == '>=':
                                plt.fill_between(x_range, y_values, 100, alpha=0.2, color='gray')
            
                except Exception as e:
                    print(f"Erro ao desenhar restrição {i + 1}: {e}")

# ------------------------------------------------------------------------------------

            # Adicionar ponto ótimo ao gráfico
            plt.scatter(optimal_point[0], optimal_point[1], color='red', s=100, label='Solução Ótima')
            plt.text(optimal_point[0], optimal_point[1], f'({optimal_point[0]}, {optimal_point[1]})', fontsize=10, color='red')

            # Determinar os limites do gráfico dinamicamente
            all_x = []
            all_y = []

            # Coletar todos os pontos das restrições
            for restriction in restriction_points:
                point1, point2 = restriction['Pontos']
                all_x.extend([point1[0], point2[0]])
                all_y.extend([point1[1], point2[1]])

            # Ajustar limites com base nas restrições de não negatividade
            if non_negativity.get('x1', True):
                min_x = 0  # Garante que x1 não será negativo
            if non_negativity.get('x2', True):
                min_y = 0  # Garante que x2 não será negativo

            # Garantir que limites negativos não sejam exibidos no gráfico
            plt.xlim(min_x if 'min_x' in locals() else min(all_x) - 1, max(all_x) + 1)
            plt.ylim(min_y if 'min_y' in locals() else min(all_y) - 1, max(all_y) + 1)

            plt.grid(color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
            plt.legend()
            plt.savefig(filepath)
            plt.close()

# ------------------------------------------------------------------------------------

            return JsonResponse({
                'Ponto Ótimo': f"({', '.join(map(str, optimal_point))})",
                'Resultado Objetivo': objective_result,
                'Pontos Restrição': restriction_points,
                'graph_path': f"/static/graph.png"
            })

        except Exception as e:
            print(f"Erro inesperado: {e}")
            return JsonResponse({'error': f"Erro inesperado: {str(e)}"}, status=500)

