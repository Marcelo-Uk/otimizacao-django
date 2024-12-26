from django.http import JsonResponse, FileResponse
from pulp import LpProblem, LpVariable, LpMaximize, LpMinimize, lpSum
import matplotlib.pyplot as plt
import os
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def optimize(request):
    # Exemplo de entrada de dados (substitua por JSON do front-end)
    data = {
        'objective': 'maximize',
        'variables': [{'name': 'x1', 'coefficient': 3}, {'name': 'x2', 'coefficient': 5}],
        'constraints': [
            {'variables': [{'name': 'x1', 'coefficient': 1}, {'name': 'x2', 'coefficient': 2}], 'type': '<=', 'rhs': 10},
            {'variables': [{'name': 'x1', 'coefficient': 3}, {'name': 'x2', 'coefficient': 1}], 'type': '<=', 'rhs': 15}
        ]
    }

    sense = LpMaximize if data['objective'] == 'maximize' else LpMinimize
    model = LpProblem('Optimization', sense)

    variables = {v['name']: LpVariable(v['name'], lowBound=0) for v in data['variables']}
    model += lpSum(v['coefficient'] * variables[v['name']] for v in data['variables']), 'Objective'

    for c in data['constraints']:
        lhs = lpSum(variables[v['name']] * v['coefficient'] for v in c['variables'])
        if c['type'] == '<=':
            model += lhs <= c['rhs']
        elif c['type'] == '>=':
            model += lhs >= c['rhs']

    model.solve()

    return JsonResponse({
        'status': str(model.status),
        'variables': {v.name: v.varValue for v in model.variables()},
        'objective': model.objective.value()
    })

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
