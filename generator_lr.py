from collections import deque, OrderedDict
import firstandfollows


# Added for Parse Tree Simulation
nt_list_global = []


nt_list = []
t_list = []

LAMBDA = 'λ'



class State:
    _id = 0

    def __init__(self, closure):
        self.closure = closure
        self.no = State._id
        State._id += 1


class Item(str):
    def __new__(cls, item, lookahead=list()):
        if '.' not in item:
            raise ValueError(f"Item mal formado, sin '.': {item}")
        self = str.__new__(cls, item)
        # Lookaheads are IGNORED for LR(0) identity
        self.lookahead = [] 
        return self

    def __str__(self):
        return super(Item, self).__str__()



def closure(items):
    def exists(newitem, items):
        # Only check the core item string since lookaheads are gone
        for i in items:
            if i == newitem:
                return True
        return False

    global production_list

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
            
            # LR(0): We DO NOT compute lookaheads from beta + la

            for prod in firstandfollows.production_list:
                lhs, rhs = prod.split('→')
                if lhs.strip() != B:
                    continue

                rhs_symbols = rhs.strip().split()
                new_body = '. ' + ' '.join(rhs_symbols)
                new_item = Item(f"{B}→{new_body}", []) # Empty lookahead

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
    
    # Filter out Lambda/Epsilon from the result to treat them as empty
    # But keep '.'
    # The generator uses 'λ' (from code constant/string)
    LAMBDA_SYMBOLS = ['λ', 'ε']
    filtered_result = [x for x in result if x not in LAMBDA_SYMBOLS]
    
    # Special case: If the body was JUST lambda/epsilon (now empty), we have [].
    # But we might have the dot.
    # If original was "A -> . λ", split gives ['.', 'λ']. Filtered gives ['.'].
    # If original was "A -> λ .", split gives ['λ', '.']. Filtered gives ['.']. 
    # This correctly reduces to "A -> ." 
    
    return filtered_result


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

def format_states_lr0(states, codigos_equivalentes={}, show_lambda=False, empty_symbol='λ'):
    result = []
    for idx, state in enumerate(states):
        result.append(f"Item{idx}{{")
        # Ensure we can handle State objects or raw lists
        items = state.closure if hasattr(state, 'closure') else state
        for item in items:
             
             head, body = item.split('→')
             
             # Sanitize body for display: Remove internal λ/ε if present
             for bad_sym in ['λ', 'ε']:
                 body = body.replace(bad_sym, "")
             
             # Handle dot and arrow
             body_display = body.replace('.', '●').strip()
             
             # If logic led to space issues, clean up multiple spaces
             body_display = " ".join(body_display.split())
             
             # Logic to show Lambda/Epsilon if body is effectively empty (only dot) and show_lambda is True
             if body_display.replace('●', '').strip() == "":
                 if show_lambda:
                     if body_display.startswith('●'):
                          body_display = f"● {empty_symbol}" 
                     else:
                          body_display = f"{empty_symbol} ●"
             
             # For LR(0), we DO NOT show lookaheads.
             
             line = f"[ {head} → {body_display} ]"
             result.append(line)
             
        result.append("}\n")
    return "\n".join(result)


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
                # For LR(0), we only care about core items (lookaheads are ignored)
                return True
                
                # Original CLR logic for reference:
                # for i in range(len(s)):
                #     if s[i].lookahead != t[i].lookahead: break
                # else:
                #     return True

        return False

    global nt_list, t_list

    head, body = firstandfollows.production_list[0].split('→')

    states = [closure([Item(head + '→.' + body, [])])]

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


def make_table(states):
    global nt_list, t_list

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

    def getprodno(item):
        head, body = item.split('→')
        body_without_dot = body.replace('.', '').strip()
        clean = head.strip() + '→' + body_without_dot
        for i, prod in enumerate(firstandfollows.production_list):
            if prod.strip() == clean:
                return i
        return -1

    SLR_Table = OrderedDict()

    for i in range(len(states)):
        states[i] = State(states[i])  # Asigna números de estado

    for s in states:
        SLR_Table[s.no] = OrderedDict()

        for item in s.closure:
            head, body = item.split('→')
            body_symbols = split_body_with_dot(body.strip())


            if body_symbols == ['.']:  # Producción completamente reducida
                # LR(0): Reduce on ALL terminals (including $)
                for term in t_list:
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
                    # LR(0): Reduce on ALL terminals
                    for term in t_list:
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

def make_table_slr(states):
    global nt_list, t_list
    
    # 1. State Object Conversion
    for i in range(len(states)):
        if not isinstance(states[i], State):
            states[i] = State(states[i])

    def getstateno(t):
        for s in states:
            if len(s.closure) != len(t):
                continue
            s_set = set(str(x) for x in s.closure)
            t_set = set(str(x) for x in t)
            if s_set == t_set:
                 return s.no
        return -1

    def getprodno(item):
        """
        Robustly finds production index by comparing token lists,
        ignoring whitespace differences.
        """
        item_head, item_body = item.split('→')
        # Remove dot and excess whitespace
        item_body_clean = item_body.replace('.', ' ').strip()
        item_tokens = item_body_clean.split()
        
        # Handle Lambda/Epsilon in item body if it was purely that
        # (Though usually formatted items keep their structure)
        
        item_head = item_head.strip()
        
        for i, prod in enumerate(firstandfollows.production_list):
            prod_head, prod_body = prod.split('→')
            prod_tokens = prod_body.strip().split()
            
            if item_head == prod_head.strip() and item_tokens == prod_tokens:
                return i
        return -1

    Table = OrderedDict()

    # Initialize Table Rows
    for s in states:
        Table[s.no] = OrderedDict()

    for s in states:
        for item in s.closure:
            head, body = item.split('→')
            body_symbols = split_body_with_dot(body.strip())

            # CASE 1: Reduce checks
            # Logic: If dot is last, or body became only '.' (from A->. or A->.λ)
            
            # Check effectively if it is a reduce item
            # We can check if 'dot' is at the end of the filtered symbols
            is_reduce = False
            if body_symbols == ['.']: 
                is_reduce = True
            elif '.' in body_symbols and body_symbols.index('.') == len(body_symbols) - 1:
                is_reduce = True
                
            if is_reduce:
                prod_idx = getprodno(item)
                
                if prod_idx == -1:
                    print(f"Warning: Could not find production for item {item}")
                    continue

                if prod_idx == 0:
                    # Accept State: S' -> S .
                    Table[s.no]['$'] = 'Aceptar'
                else:
                    # SLR(1) Logic: Reduce only on Follow(Head)
                    follow_set = firstandfollows.get_siguiente(head.strip())
                    
                    if not follow_set:
                        # Should not happen for reachable non-terminals, but safety check
                        continue

                    for term in follow_set:
                        if term not in Table[s.no].keys():
                            Table[s.no][term] = {'r' + str(prod_idx)}
                        else:
                            val = Table[s.no][term]
                            if isinstance(val, set):
                                val.add('r' + str(prod_idx))
                            else:
                                Table[s.no][term] = {val, 'r' + str(prod_idx)}
                continue

            # CASE 2: Shift or Goto
            try:
                if '.' in body_symbols:
                    dot_pos = body_symbols.index('.')
                    if dot_pos + 1 < len(body_symbols):
                        nextsym = body_symbols[dot_pos + 1]
                        
                        t = goto(s.closure, nextsym)
                        if t != []:
                            next_state_id = getstateno(t)
                            
                            if nextsym in t_list:
                                # SHIFT
                                action = 's' + str(next_state_id)
                                if nextsym not in Table[s.no].keys():
                                    Table[s.no][nextsym] = {action}
                                else:
                                     val = Table[s.no][nextsym]
                                     if isinstance(val, set):
                                         val.add(action)
                                     else:
                                         Table[s.no][nextsym] = {val, action}
                            else:
                                # GOTO
                                Table[s.no][nextsym] = str(next_state_id)
                        
            except ValueError:
                 pass
            except IndexError:
                 pass
                 
    return Table


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
    global production_list, ntl, nt_list, tl, t_list

    print("Ingresa los símbolos NO TERMINALES separados por |:")
    non_terminal_input = input().strip()
    non_terminal_symbols = non_terminal_input.split('|')

    firstandfollows.nt_list.clear()
    for nt in non_terminal_symbols:
        firstandfollows.nt_list[nt] = firstandfollows.NonTerminal(nt)

    print("\nIngresa los símbolos TERMINALES separados por |:")
    terminal_input = input().strip()
    terminal_symbols = terminal_input.split('|')

    firstandfollows.t_list.clear()
    for term in terminal_symbols:
        firstandfollows.t_list[term] = firstandfollows.Terminal(term)

    print("\nPega tus producciones (una por línea).")
    print("Cuando termines, presiona Enter en una línea vacía:")

    user_productions = []
    try:
        while True:
            line = input()
            if line.strip() == "":
                break
            user_productions.append(line.strip())
    except EOFError:
        pass  # Por si usas redirección o termina entrada con Ctrl+D (Linux/Mac)

    if not user_productions:
        print("No se ingresaron producciones. Finalizando.")
        return

    # Toda la salida en .txt
    with open("salida_clr1.txt", "w", encoding="utf-8") as f:
        original_stdout = sys.stdout
        sys.stdout = f  # Redirige toda la salida print al archivo
    # Aqui acaba
    production_list[:] = user_productions

    firstandfollows.main(production_list)

    print("\tPRIMERO Y SIGUIENTE DE NO TERMINALES")
    
    firstandfollows.compute_all_primeros()
    firstandfollows.compute_all_siguientes()
    
    for nt in ntl:
        first = sorted(firstandfollows.get_primero(nt))
        follow = sorted(firstandfollows.get_siguiente(nt))
        print(nt)
        print("\tPrimero:\t", firstandfollows.get_primero(nt))
        print("\tSiguiente:\t", firstandfollows.get_siguiente(nt), "\n")

    augment_grammar()

    nt_list = list(ntl.keys())
    t_list = list(tl.keys()) + ['$']

    print(nt_list)
    print(t_list, "\n")

    j = calc_states()

    #CON ESTE EXPORTAMOS EN PDF
    #export_items_to_pdf(j, codigos_equivalentes, filename="items_clr1.pdf")

    ctr = 0
    for idx, state in enumerate(j):
        print(f"Item{idx}{{")  # ACA SER CAMBIA EL ITEM POR I SI QUIERES
        pretty_print_items(state, codigos_equivalentes)
        print("}\n")

    table = make_table(j)

    print("\n\tCLR(1) TABLE\n")

    sr, rr = 0, 0

    for i, fila in table.items():
        print(i, "\t", fila)
        shift_count, reduce_count = 0, 0

        for simbolo, acciones in fila.items():
            if acciones == 'Aceptar':
                continue
            if isinstance(acciones, set) and len(acciones) > 1:
                acciones_list = list(acciones)

                tipos = {'shift': 0, 'reduce': 0}
                for accion in acciones_list:
                    if accion.startswith('s'):
                        tipos['shift'] += 1
                    elif accion.startswith('r'):
                        tipos['reduce'] += 1

                # Mostrar nombre del símbolo si existe en el diccionario
                simbolo_legible = codigos_equivalentes.get(simbolo, simbolo)

                if tipos['shift'] > 0 and tipos['reduce'] > 0:
                    sr += 1
                    print(f"⚠️ SR conflict en estado {i}, símbolo '{simbolo_legible}' => acciones: {acciones_list}")
                elif tipos['reduce'] > 1:
                    rr += 1
                    print(f"⚠️ RR conflict en estado {i}, símbolo '{simbolo_legible}' => acciones: {acciones_list}")

    print("\n", sr, "s/r conflicts |", rr, "r/r conflicts")
    #export_table_as_csv_format(table)

    # EXPORTAR TABLA COMO .CSV
    #export_clr1_table_full_csv(table, "tabla_clr1_completa.csv")

    # EXPORTAR SALIDA COMO .TXT
    #sys.stdout = original_stdout  # Restaurar salida estándar
    #print("✅ Archivo 'salida_clr1.txt' generado correctamente.")
    return

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

def export_lr0_items_to_pdf(states, filename="states_lr0.pdf", show_lambda=False, empty_symbol='λ'):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    margin = inch
    y = height - margin
    c.setFont("Times-Roman", 12)

    for idx, state in enumerate(states):
        titulo = f"Item{idx}{{"
        
        # Page break check
        if y < margin:
             c.showPage()
             c.setFont("Times-Roman", 12)
             y = height - margin
             
        c.drawString(margin, y, titulo)
        y -= 16

        for item in (state.closure if hasattr(state, 'closure') else state):
             head, body = item.split('→')
             
             # Sanitize
             for bad_sym in ['λ', 'ε']:
                 body = body.replace(bad_sym, "")
             
             body_display = body.replace('.', '●').strip()
             body_display = " ".join(body_display.split())
             
             if body_display.replace('●', '').strip() == "":
                 if show_lambda:
                     if body_display.startswith('●'):
                          body_display = f"● {empty_symbol}" 
                     else:
                          body_display = f"{empty_symbol} ●"
             
             line = f"[ {head} -> {body_display} ]"

             wrapped_lines = textwrap.wrap(line, width=90)
             for wrapped_line in wrapped_lines:
                 if y < margin:
                     c.showPage()
                     c.setFont("Times-Roman", 12)
                     y = height - margin
                 c.drawString(margin, y, wrapped_line)
                 y -= 14
        
        # Closing brace
        if y < margin:
            c.showPage()
            c.setFont("Times-Roman", 12)
            y = height - margin
        c.drawString(margin, y, "}")
        y -= 20

    c.save()
    print(f"✅ PDF generado: {filename}")


def parse(table, input_string):
    """
    Simulates LR(0) parsing for the given input string.
    Returns a list of steps, where each step is a dict:
    {
        'stack': str,   # State Stack
        'symbols': str, # Symbol Stack
        'input': str,   # Input Buffer
        'action': str   # Action Taken
    }
    """
    global production_list
    
    # 1. Tokenize Input
    tokens = input_string.strip().split()
    tokens.append('$') # Append EOF
    
    # 2. Initialize Stacks
    state_stack = [0]
    symbol_stack = [] # Removed '$' as requested by user
    
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
        
        # Look up action
        # Table format: table[state_id][symbol] = {'sN'} or {'rN'} or 'Aceptar'
        
        row = table.get(current_state, {})
        action_set = row.get(current_input)
        
        if not action_set:
            steps[step_idx]['action'] = f"Error: No action for input '{current_input}' in state {current_state}"
            return steps # Fail
            
        # Resolve Set
        # If conflict, we just take the first one for simulation purposes or error
        if isinstance(action_set, set):
            action = list(action_set)[0]
            if len(action_set) > 1:
                steps[step_idx]['action'] = f"Conflict: {action_set}. Chose {action}"
        else:
            action = action_set # Could be 'Aceptar' string directly based on logic
            
        # Execute Action
        if action == 'Aceptar':
            steps[step_idx]['action'] = "Accept"
            accepted = True
            break
            
        elif action.startswith('s'):
            # SHIFT
            next_state = int(action[1:])
            
            steps[step_idx]['action'] = f"Shift {next_state}"
            
            state_stack.append(next_state)
            symbol_stack.append(current_input)
            cursor += 1
            
        elif action.startswith('r'):
            # REDUCE
            prod_idx = int(action[1:])
            production = production_list[prod_idx]
            lhs, rhs = production.split('→')
            lhs = lhs.strip()
            rhs_body = rhs.strip()
            
            # Determine RHS length (beta)
            # Handle Lambda/Epsilon
            rhs_symbols = []
            if rhs_body not in ['λ', 'ε', '']:
                 rhs_symbols = rhs_body.split()
            
            count_to_pop = len(rhs_symbols)
            
            # Pop from stacks
            if count_to_pop > 0:
                state_stack = state_stack[:-count_to_pop]
                symbol_stack = symbol_stack[:-count_to_pop]
            
            # Note: Do not advance cursor
            
            # GOTO
            top_state = state_stack[-1]
            goto_row = table.get(top_state, {})
            goto_state_raw = goto_row.get(lhs)
            
            if not goto_state_raw:
                steps[step_idx]['action'] = f"Reduce {prod_idx} ({production}), but GOTO error on [{top_state}, {lhs}]"
                return steps
                
            # Goto could be a set or string/int depending on how make_table saves NTs
            # In make_table: SLR_Table[s.no][nextsym] = str(getstateno(t)) (string)
            if isinstance(goto_state_raw, set):
                 goto_state = int(list(goto_state_raw)[0])
            else:
                 goto_state = int(goto_state_raw)
                 
            state_stack.append(goto_state)
            symbol_stack.append(lhs)
            
            steps[step_idx]['action'] = f"Reduce {prod_idx}: {production}"
            
        else:
            steps[step_idx]['action'] = f"Unknown action: {action}"
            return steps
            
        step_count += 1
        
    if not accepted and step_count >= max_steps:
         steps.append({
            'stack': "...",
            'symbols': "...",
            'input': "...",
            'action': "Terminated: Max steps reached"
        })
        
    return steps


if __name__ == "__main__":
    main()
