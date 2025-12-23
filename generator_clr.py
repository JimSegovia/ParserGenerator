from collections import OrderedDict
import firstandfollows

# Standardized aliases
nt_list = []
t_list = []


class State:
    _id = 0

    def __init__(self, closure):
        self.closure = closure
        self.no = State._id
        State._id += 1


class Item(str):
    def __new__(cls, item, lookahead=None):
        if '.' not in item:
            raise ValueError(f"Item mal formado, sin '.': {item}")
        self = str.__new__(cls, item)
        self.lookahead = sorted(list(lookahead)) if lookahead else []
        return self

    def __str__(self):
        return super(Item, self).__str__() + ", " + '|'.join(self.lookahead)

    def __eq__(self, other):
        if not isinstance(other, Item):
            return False
        return str(self) == str(other) and self.lookahead == other.lookahead

    def __hash__(self):
        return hash((str(self), tuple(self.lookahead)))



def closure(items):
    def exists(newitem, items):
        for i in items:
            if i == newitem: # Uses __eq__ which checks lookahead
                return True
        return False

    global nt_list
    while True:
        flag = 0
        for i in items:
            head, body = i.split('→')
            symbols = split_body_with_dot(body.strip())

            if '.' not in symbols or symbols.index('.') == len(symbols) - 1:
                continue

            dot_pos = symbols.index('.')
            B = symbols[dot_pos + 1]  # símbolo después del punto

            if B not in nt_list:
                continue

            beta = symbols[dot_pos + 2:]  # lo que sigue después de B
            lookaheads = set()

            for la in i.lookahead:
                sequence = beta + [la]
                result = firstandfollows.compute_first_sequence(sequence)
                lookaheads.update(result)

            for prod in firstandfollows.production_list:
                lhs, rhs = prod.split('→')
                if lhs.strip() != B:
                    continue

                rhs_symbols = rhs.strip().split()
                new_body = '. ' + ' '.join(rhs_symbols)
                new_item = Item(f"{B}→{new_body}", lookaheads)

                if not exists(new_item, items):
                    items.append(new_item)
                    flag = 1

        if not flag:
            break

    return items

def split_body_with_dot(body):
    result = []
    i = 0
    while i < len(body):
        if body[i] == '.':
            result.append('.')
            i += 1
        elif body[i] == ' ':
            i += 1  # ignora espacios extra
        else:
            sym = ''
            while i < len(body) and body[i] not in ['.', ' ']:
                sym += body[i]
                i += 1
            result.append(sym)
    return result


def pretty_print_items(items, codigos_equivalentes={}):
    for item in items:
        # Remplaza '.' por '●' solo para mostrar
        item_str = item.replace('.', '●').replace('→', '->')

        # Reemplazar símbolos codificados por su forma legible
        if codigos_equivalentes:
            for codigo, texto in codigos_equivalentes.items():
                item_str = item_str.replace(codigo, texto)

        for lookahead in item.lookahead:
            lookahead_str = codigos_equivalentes.get(lookahead, lookahead) if codigos_equivalentes else lookahead
            print(f"[ {item_str}, {lookahead_str} ]")


def format_states(states, codigos_equivalentes={}):
    """
    Returns a formatted string of all states for GUI display.
    """
    output = []
    for idx, state in enumerate(states):
        output.append(f"State {idx}:")
        
        # Determine items list
        items = state.closure if hasattr(state, 'closure') else state
        
        for item in items:
            # Remplaza '.' por '●' solo para mostrar
            item_str = item.replace('.', '●').replace('→', '->')

            # Reemplazar símbolos codificados por su forma legible
            if codigos_equivalentes:
                for codigo, texto in codigos_equivalentes.items():
                    item_str = item_str.replace(codigo, texto)
            
            # Format lookaheads
            lookaheads = item.lookahead
            # Join lookaheads with spaces or commas? The original printed one line per lookahead?
            # Original: for lookahead in item.lookahead: print(...)
            # Let's verify original logic.
            
            for lookahead in lookaheads:
                lookahead_str = codigos_equivalentes.get(lookahead, lookahead) if codigos_equivalentes else lookahead
                output.append(f"  [ {item_str}, {lookahead_str} ]")
        
        output.append("") # Empty line between states
        
    return "\n".join(output)


def goto(items, symbol):
    initial = []

    for i in items:
        head, body = i.split('→')
        symbols = split_body_with_dot(body.strip())

        if '.' not in symbols:
            continue

        dot_pos = symbols.index('.')

        # Verificamos si hay símbolo después del punto
        if dot_pos + 1 < len(symbols) and symbols[dot_pos + 1] == symbol:
            # Mover el punto a la derecha del símbolo actual
            new_symbols = symbols[:dot_pos] + [symbol, '.'] + symbols[dot_pos + 2:]
            new_body = ' '.join(new_symbols)
            initial.append(Item(f"{head}→{new_body}", i.lookahead))

    return closure(initial)



def calc_states():
    def contains(states, t):

        for s in states:
            if len(s) != len(t): continue

            if sorted(s) == sorted(t):
                for i in range(len(s)):
                    if s[i].lookahead != t[i].lookahead: break
                else:
                    return True

        return False

    global nt_list, t_list

    head, body = firstandfollows.production_list[0].split('→')

    states = [closure([Item(head + '→.' + body, ['$'])])]

    while True:
        flag = 0
        for s in states:

            for e in nt_list + t_list:

                t = goto(s, e)
                if t == [] or contains(states, t): continue

                states.append(t)
                flag = 1

        if not flag: break

    return states



def getprodno(item):
    head, body = item.split('→')
    body_without_dot = body.replace('.', '').strip()
    
    for i, prod in enumerate(firstandfollows.production_list):
        p_head, p_body = prod.split('→')
        if p_head.strip() == head.strip() and p_body.strip() == body_without_dot:
            return i
    return -1

def make_table(states):
    global nt_list, t_list
    State._id = 0 # Reset for consistent numbering

    def getstateno(t):
        for s in states:
            if len(s.closure) != len(t):
                continue
            if sorted(s.closure) == sorted(t):
                for i in range(len(s.closure)):
                    if s.closure[i].lookahead != t[i].lookahead:
                        break
                else:
                    return s.no
        return -1

    SLR_Table = OrderedDict()

    # Crucial: Reset numbering and wrap only if needed
    for i in range(len(states)):
        if not isinstance(states[i], State):
            states[i] = State(states[i])
        else:
            # Re-assign numbers if we want them to start from 0 every build
            states[i].no = i # Or rely on State._id if we reconstructed them
            # Actually, to be safe and consistent:
            states[i].no = State._id
            State._id += 1

    for s in states:
        SLR_Table[s.no] = OrderedDict()

        for item in s.closure:
            head, body = item.split('→')
            body_symbols = split_body_with_dot(body.strip())


            if body_symbols == ['.']:  # Producción completamente reducida
                for term in item.lookahead:
                    if term not in SLR_Table[s.no].keys():
                        SLR_Table[s.no][term] = {'r' + str(getprodno(item))}
                    else:
                        SLR_Table[s.no][term] |= {'r' + str(getprodno(item))}
                continue

            try:
                dot_pos = body_symbols.index('.')
            except ValueError:
                raise ValueError(f"Producción inválida sin punto: {item}")

            if dot_pos == len(body_symbols) - 1:
                # Punto al final (producción lista para reducir)
                if getprodno(item) == 0:
                    SLR_Table[s.no]['$'] = 'Aceptar'
                else:
                    for term in item.lookahead:
                        if term not in SLR_Table[s.no].keys():
                            SLR_Table[s.no][term] = {'r' + str(getprodno(item))}
                        else:
                            SLR_Table[s.no][term] |= {'r' + str(getprodno(item))}
                continue

            # Punto no al final: shift o goto
            nextsym = body_symbols[dot_pos + 1]
            t = goto(s.closure, nextsym)
            if t != []:
                if nextsym in t_list:
                    if nextsym not in SLR_Table[s.no].keys():
                        SLR_Table[s.no][nextsym] = {'s' + str(getstateno(t))}
                    else:
                        SLR_Table[s.no][nextsym] |= {'s' + str(getstateno(t))}
                else:
                    SLR_Table[s.no][nextsym] = str(getstateno(t))

    return SLR_Table

def parse(table, input_string):
    """
    Simulates CLR(1) parsng for the given input string.
    Identical logic to LR(0)/SLR(1) parsing if the table is built correctly.
    Supports both integer state IDs (CLR/LR0/SLR) and string state IDs (LALR).
    """
    # 1. Tokenize Input
    tokens = input_string.strip().split()
    tokens.append('$') # Append EOF
    
    # 2. Determine State Type from Table Keys
    # LALR uses string keys like "36", others use ints like 0
    first_key = list(table.keys())[0] if table else 0
    use_string_states = isinstance(first_key, str)
    
    # Initialize Stacks
    initial_state = "0" if use_string_states else 0
    # Search for start state if it's not 0 or "0" (LALR "0" might be something else if sorted differently?)
    # Usually state 0 is correct for start.
    
    state_stack = [initial_state]
    symbol_stack = [] 
    
    steps = []
    
    cursor = 0
    max_steps = 1000 # Safety break
    step_count = 0
    
    accepted = False
    
    while step_count < max_steps:
        current_state = state_stack[-1]
        current_input = tokens[cursor]
        
        # Snapshot state
        steps.append({
            'stack': " ".join(map(str, state_stack)),
            'symbols': " ".join(symbol_stack),
            'input': " ".join(tokens[cursor:]),
            'action': ""
        })
        
        step_idx = len(steps) - 1
        
        row = table.get(current_state, {})
        action_set = row.get(current_input)
        
        if not action_set:
            steps[step_idx]['action'] = f"Error: No action for input '{current_input}' in state {current_state}"
            return steps # Fail
            
        if isinstance(action_set, set):
            action = list(action_set)[0]
            if len(action_set) > 1:
                steps[step_idx]['action'] = f"Conflict: {action_set}. Chose {action}"
        else:
            action = action_set 
            
        if action == 'Aceptar':
            steps[step_idx]['action'] = "Accept"
            accepted = True
            break
            
        elif action.startswith('s'):
            # SHIFT
            next_state_raw = action[1:]
            
            if use_string_states:
                next_state = str(next_state_raw)
            else:
                next_state = int(next_state_raw)
                
            steps[step_idx]['action'] = f"Shift {next_state}"
            state_stack.append(next_state)
            symbol_stack.append(current_input)
            cursor += 1
            
        elif action.startswith('r'):
            # REDUCE
            prod_idx = int(action[1:])
            production = firstandfollows.production_list[prod_idx]
            head, body = production.split('→')
            head = head.strip()
            body = body.strip()
            
            # Handle Lambda
            body_symbols = body.split()
            if body in ['λ', 'ε', '']:
                body_symbols = []
            
            count_to_pop = len(body_symbols)
            
            if count_to_pop > 0:
                state_stack = state_stack[:-count_to_pop]
                symbol_stack = symbol_stack[:-count_to_pop]
            
            # GOTO
            top_state = state_stack[-1]
            goto_row = table.get(top_state, {})
            goto_state_raw = goto_row.get(head)
            
            if not goto_state_raw:
                steps[step_idx]['action'] = f"Reduce {prod_idx} ({production}), but GOTO error on [{top_state}, {head}]"
                return steps
                
            if isinstance(goto_state_raw, set):
                 goto_val = list(goto_state_raw)[0]
            else:
                 goto_val = goto_state_raw
            
            if use_string_states:
                goto_state = str(goto_val)
            else:
                goto_state = int(goto_val)
                 
            state_stack.append(goto_state)
            symbol_stack.append(head)
            steps[step_idx]['action'] = f"Reduce {prod_idx}: {production}"
            
        else:
            steps[step_idx]['action'] = f"Unknown action: {action}"
            return steps
            
        step_count += 1
        
    return steps

def augment_grammar():
    for i in range(ord('Z'), ord('A') - 1, -1):
        new_start = chr(i)
        if new_start not in firstandfollows.nt_list:
            start_prod = firstandfollows.production_list[0]
            firstandfollows.production_list.insert(0, new_start + '→' + start_prod.split('→')[0])
            firstandfollows.nt_list[new_start] = firstandfollows.NonTerminal(new_start)
            return

import sys
def main():
    # Modularized main for testing, but typically called from GUI
    global nt_list, t_list
    pass

def export_table_as_csv_format(table):
    print("estado,símbolo,acción")  # Encabezado CSV
    for estado, fila in table.items():
        for simbolo, accion in fila.items():
            # Buscar si el símbolo tiene código equivalente
            simbolo_codificado = simbolo
            for cod, nombre in codigos_equivalentes.items():
                if nombre == simbolo:
                    simbolo_codificado = cod
                    break

            # Imprimir cada acción, incluso si hay múltiples (conflictos)
            if isinstance(accion, set):
                for a in accion:
                    print(f"{estado},{simbolo_codificado},{a}")
            else:
                print(f"{estado},{simbolo_codificado},{accion}")

import csv

def export_clr1_table_full_csv(table, filename="tabla_clr1_completa.csv"):
    # 1. Obtener todos los símbolos legibles posibles para usar como encabezados
    all_symbols = set()
    for fila in table.values():
        all_symbols.update(fila.keys())

    # Convertir a símbolos legibles
    encabezado = ["estado"] + [codigos_equivalentes.get(s, s) for s in sorted(all_symbols)]

    # 2. Escribir CSV
    with open(filename, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(encabezado)

        for estado, fila in table.items():
            fila_csv = [estado]
            for simbolo in sorted(all_symbols):
                accion = fila.get(simbolo, "")
                if isinstance(accion, set):
                    accion_str = '|'.join(sorted(accion))
                else:
                    accion_str = accion
                fila_csv.append(accion_str)
            writer.writerow(fila_csv)

    print(f"✅ Tabla CLR(1) exportada como CSV en: {filename}")

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import textwrap

def format_states(states, codigos_equivalentes={}, show_lambda=False, empty_symbol='λ'):
    """
    Returns a formatted string of all states for GUI display.
    """
    output = []
    for idx, state in enumerate(states):
        output.append(f"State {idx}:")
        
        # Determine items list
        items = state.closure if hasattr(state, 'closure') else state
        
        for item in items:
            # Remplaza '.' por '●' solo para mostrar
            item_str = item.replace('.', '●').replace('→', '->')

            # Reemplazar símbolos codificados por su forma legible
            if codigos_equivalentes:
                for codigo, texto in codigos_equivalentes.items():
                    item_str = item_str.replace(codigo, texto)
            
            # Logic to show Lambda/Epsilon if body is effectively empty (only dot) and show_lambda is True
            # Split by -> to get LHS and RHS
            if "->" in item_str:
                lhs, rhs = item_str.split("->", 1)
                rhs = rhs.strip()
                # Remove internal λ/ε from RHS if present (though standardized code shouldn't have them)
                for bad in ['λ', 'ε']: rhs = rhs.replace(bad, "")
                
                if rhs.replace('●', '').strip() == "":
                    if show_lambda:
                        if rhs.startswith('●'):
                            rhs = f"● {empty_symbol}"
                        else:
                            rhs = f"{empty_symbol} ●"
                item_str = f"{lhs}-> {rhs}"

            # Format lookaheads
            lookaheads = item.lookahead
            for lookahead in lookaheads:
                lookahead_str = codigos_equivalentes.get(lookahead, lookahead) if codigos_equivalentes else lookahead
                output.append(f"  [ {item_str}, {lookahead_str} ]")
        
        output.append("") # Empty line between states
        
    return "\n".join(output)


def export_items_to_pdf(states, codigos_equivalentes, filename="items_clr1.pdf", show_lambda=False, empty_symbol='λ'):
    c = canvas.Canvas(filename, pagesize=A4)

    width, height = A4
    margin = inch
    y = height - margin

    c.setFont("Times-Roman", 12)

    for idx, state in enumerate(states):
        # Título del estado
        titulo = f"Item{idx}{{"
        c.drawString(margin, y, titulo)
        y -= 16

        items = state.closure if hasattr(state, 'closure') else state
        for item in items:
            # Preparar el string legible
            item_str = item.replace(".", "●").replace("→", "->")
            for codigo, texto in codigos_equivalentes.items():
                item_str = item_str.replace(codigo, texto)

            if "->" in item_str:
                lhs, rhs = item_str.split("->", 1)
                rhs = rhs.strip()
                for bad in ['λ', 'ε']: rhs = rhs.replace(bad, "")
                if rhs.replace('●', '').strip() == "":
                    if show_lambda:
                        if rhs.startswith('●'):
                            rhs = f"● {empty_symbol}"
                        else:
                            rhs = f"{empty_symbol} ●"
                item_str = f"{lhs}-> {rhs}"

            for la in item.lookahead:
                la_str = codigos_equivalentes.get(la, la)
                line = f"[ {item_str}, {la_str} ]"

                # 🔽 Ajustamos si la línea es demasiado larga (Aprox 90 caracteres por línea)
                wrapped_lines = textwrap.wrap(line, width=90)
                for wrapped_line in wrapped_lines:
                    if y < margin:
                        c.showPage()
                        c.setFont("Times-Roman", 12)
                        y = height - margin
                    c.drawString(margin, y, wrapped_line)
                    y -= 14

        # Cierre de bloque
        if y < margin:
            c.showPage()
            c.setFont("Times-Roman", 12)
            y = height - margin
        c.drawString(margin, y, "}")
        y -= 20

    c.save()
    print(f"✅ PDF generado: {filename}")


if __name__ == "__main__":
    main()
