import os
import datetime

mode = None
# identifying which solvers we have installed
try:
    from lpsolve55 import *
    mode = 'lpsolve'
    print('lpsolve supported')
except:
    print('lpsolve not supported')
try:
    import gurobipy as grb
    mode = 'gurobi'
    print('gurobi supported')
except:
    print('gurobi not supported')
try:
    import cplex
    from cplex.exceptions import CplexSolverError
    mode = 'cplex'
    print('cplex supported')
except:
    print('CPLEX not supported')

import numpy as np
import sys
import os

class ModelFile():
    def __init__(self, filename, name, mode='cplex', stdout=sys.stdout, threads=1):
        assert stdout in [os.devnull, sys.stdout, 'log']
        self.name = name
        self.filename = filename
        self.file = open(filename + '.lp', 'w') # open with 'w' flag to write over existing file
        self.mode = mode
        self.integer = ''
        self.binary = ''
        self.optimizer_version = ''
        if self.mode == 'cplex':
            self.optimizer_version = cplex.Cplex().get_version()
        self.stdout = stdout
        self.threads = threads
        if self.mode in ['cplex', 'gurobi']:
            self.comment_start = '\\'
            self.comment_end = '\n'
            self.line_end = '\n'
        elif self.mode == 'lpsolve':
            self.comment_start = '/*'
            self.comment_end = '*/\n'
            self.line_end = ';\n'
        else:
            raise ValueError('mode configured incorrectly')

        self.comment(f'Date creation: {datetime.datetime.now(datetime.timezone.utc)} UTC')
        self.comment(f'Host: {os.uname()[1]}')
        self.start_solving = None
        self.end_solving = None
            
    def minimize(self, write):
        if self.mode in ['cplex', 'gurobi']:
            self.write(f'minimize {write}')
            self.write('subject to')
        elif self.mode == 'lpsolve':
            self.write(f'min: {write}')
            
    def maximize(self, write):
        if self.mode in ['cplex', 'gurobi']:
            self.write(f'maximize {write}')
            self.write('subject to')
        elif self.mode == 'lpsolve':
            self.write(f'max: {write}')
            
    def comment(self, comment):
        self.file.write(f'{self.comment_start} {comment} {self.comment_end}')
        
    def write(self, write, end=True):
        self.file.write(f'{write}{self.line_end if end is True else ""}')
        
    def new_line(self):
        self.file.write(self.line_end)
        
    def bounds(self):
        if self.mode in ['cplex', 'gurobi']:
            self.write('Bounds')
        
    def binary_variables(self, variables):
        self.binary += ' ' + variables + ' '
        if self.mode in ['cplex', 'gurobi']:
            self.write('Binary')
            self.write(variables.strip().replace(' ', '\n'))
        elif self.mode == 'lpsolve':
            self.write(f'bin {variables.strip()}')
            
    def int_variables(self, variables):
        self.integer += ' ' + variables + ' '
        if self.mode in ['cplex', 'gurobi']:
            self.write('General')
            self.write(variables.strip().replace(' ', '\n'))
        elif self.mode == 'lpsolve':
            self.write(f'int {variables.strip()}')
        
    def close(self):
        if self.mode in ['cplex', 'gurobi']:
            self.write('End')
        self.file.close()
        
    def solve_pool(self, gap=0.1):
        self.start_solving = datetime.datetime.now(datetime.timezone.utc)
        if self.mode == 'cplex':
            c = cplex.Cplex()
            c.parameters.threads.set(self.threads)
            if self.stdout == os.devnull:
                c.set_results_stream(open(os.devnull, 'w'))
                c.set_log_stream(open(os.devnull, 'w'))
            elif self.stdout == sys.stdout:
                c.set_results_stream(sys.stdout)
                c.set_log_stream(sys.stdout)
            elif self.stdout == 'log':
                out = open(self.filename + '.log', 'w')
                c.set_results_stream(out)
                c.set_log_stream(out)

            c.read(self.filename + '.lp')

            try:
                c.solve()
                self.end_solving = datetime.datetime.now(datetime.timezone.utc)
            except CplexSolverError:
                print("Exception raised during solve")
                return None

            status = c.solution.get_status()
            if status == c.solution.status.unbounded:
                print("Model is unbounded")
                return None

            if status == c.solution.status.infeasible:
                print("Model is infeasible")
                return None

            if status == c.solution.status.infeasible_or_unbounded:
                print("Model is infeasible or unbounded")
                return None

            variables = []
            variables.append({})
            variables[0]['objective_value'] = c.solution.get_objective_value()
            if status == c.solution.status.optimal or status == c.solution.status.MIP_optimal:
                for name, value in zip(c.variables.get_names(), c.solution.get_values()):
                    variables[0][name] = np.absolute(np.rint(value))
            
                c.parameters.mip.pool.relgap.set(gap)
                c.populate_solution_pool()
                names = c.solution.pool.get_names()
                for sol in range(c.solution.pool.get_num()):
                    variables.append({})
                    variables[sol+1]['objective_value'] = c.solution.pool.get_objective_value(sol)
                    for name, value in zip(c.variables.get_names(), c.solution.pool.get_values(sol)):
                        variables[sol+1][name] = np.absolute(np.rint(value))
            return variables
        elif self.mode == 'gurobi':
            self.end_solving = datetime.datetime.now(datetime.timezone.utc)
            return None
        elif self.mode == 'lpsolve':
            self.end_solving = datetime.datetime.now(datetime.timezone.utc)
            return None
        
    def solve(self):
        self.start_solving = datetime.datetime.now(datetime.timezone.utc)
        if self.mode == 'cplex':
            c = cplex.Cplex()
            c.parameters.threads.set(self.threads)
            if self.stdout == os.devnull:
                c.set_results_stream(open(os.devnull, 'w'))
                c.set_log_stream(open(os.devnull, 'w'))
            elif self.stdout == sys.stdout:
                c.set_results_stream(sys.stdout)
                c.set_log_stream(sys.stdout)
            elif self.stdout == 'log':
                out = open(self.filename + '.log', 'w')
                c.set_results_stream(out)
                c.set_log_stream(out)

            c.read(self.filename + '.lp')

            try:
                c.solve()
                self.end_solving = datetime.datetime.now(datetime.timezone.utc)
            except CplexSolverError:
                print("Exception raised during solve")
                return None

            status = c.solution.get_status()
            if status == c.solution.status.unbounded:
                print("Model is unbounded")
                return None

            if status == c.solution.status.infeasible:
                print("Model is infeasible")
                return None

            if status == c.solution.status.infeasible_or_unbounded:
                print("Model is infeasible or unbounded")
                return None

            self.variables = {}
            self.variables['objective_value'] = c.solution.get_objective_value()
            if status == c.solution.status.optimal or status == c.solution.status.MIP_optimal:
                print('Model solved successfully!')
                for name, value in zip(c.variables.get_names(), c.solution.get_values()):
                    if ' ' + name + ' ' in self.binary or ' ' + name + ' ' in self.integer:
                        self.variables[name] = int(np.rint(value))
                    else:
                        self.variables[name] = value
            return self.variables
        elif self.mode == 'gurobi':
            gurobi_env = grb.Env()
            gurobi_env.setParam('Threads', self.threads)
            if self.stdout == os.devnull:
                gurobi_env.setParam('OutputFlag', 0)
            elif self.stdout == sys.stdout:
                gurobi_env.setParam('OutputFlag', 1)
            elif self.stdout == 'log':
                gurobi_env.setParam('OutputFlag', 0)
                gurobi_env.setParam('LogFile', self.filename + '.log')
            
            model = grb.read(self.filename + '.lp', gurobi_env)
            model.optimize()
            self.end_solving = datetime.datetime.now(datetime.timezone.utc)

            if model.status == grb.GRB.Status.INFEASIBLE:
                print('Optimization was stopped with status %d' % model.status, 'infeasible')
                return None
            elif model.status == grb.GRB.Status.OPTIMAL:
                print('model solved successfully')
                self.variables = {}
                solution_vars = model.getVars()
#                 print('solution vars', len(solution_vars))
                for var in solution_vars:
                    if ' ' + name + ' ' in self.binary or ' ' + name + ' ' in self.integer:
                        self.variables[var.varName] = int(np.rint(var.x))
                    else:
                        self.variables[var.varName] = var.x
                return self.variables
            else:
                print('model was not optimized')
                return None
        elif self.mode == 'lpsolve':
            lp = lpsolve('read_lp_file', self.filename + '.lp')
            lpsolve('set_lp_name', lp, self.name)
            status = lpsolve('solve', lp)
            self.end_solving = datetime.datetime.now(datetime.timezone.utc)
            if status == 3:
                print("Model is unbounded")
                return
            if status == 2:
                print("Model is infeasible")
                return
            if status == 4:
                print("The model is degenerative")
                return
            if status == -2:
                print("Out of memory")
                return
            if status == 1:
                print("The model is sub-optimal")
                return
            if status == 4:
                print("The model is degenerative")
                return
            if status == 5:
                print("Numerical failure encountered")
                return
            if status == 25:
                print("Accuracy error encountered")
                return
            
            self.variables = {}
            for name, value in zip(lpsolve('get_col_names', lp), lpsolve('get_solution', lp)[1]):
                if ' ' + name + ' ' in self.binary or ' ' + name + ' ' in self.integer:
                    self.variables[name] = int(np.rint(value))
                else:
                    self.variables[name] = value
            lpsolve('delete_lp', lp)
            return self.variables
        
    def write_solution(self):
        with open(self.filename + '.sol', 'w') as f:
            solving_time = self.end_solving - self.start_solving # datetime.timedelta
            print(f'# start time: {self.start_solving}', file=f)
            print(f'# finish time: {self.end_solving}', file=f)
            print(f'# computer: {os.uname()[1]}', file=f)
            print(f'# solving time: {solving_time}', file=f)
            print(f'# solving time (seconds): {solving_time.total_seconds()}', file=f)
            print(f'# {mode} version: {self.optimizer_version}', file=f)
            for name, value in self.variables.items():
                print(f'{name} {value}', file=f)

