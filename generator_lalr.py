
import generator_clr
import firstandfollows
from collections import OrderedDict, defaultdict

class LALRState:
    def __init__(self, states_to_merge):
        # states_to_merge: list of generator_clr.State
        
        # 1. Calculate combined ID
        # Sort by ID ensures deterministic name "36", not "63"
        self.sorted_states = sorted(states_to_merge, key=lambda s: s.no)
        self.original_ids = [s.no for s in self.sorted_states]
        
        # Name: concatenation of IDs
        self.no = "".join(str(s.no) for s in self.sorted_states)
        
        # 2. Merge lookaheads
        self.closure = []
        
        # Group items by their core string
        core_map = defaultdict(set)
        
        for state in self.sorted_states:
            items = state.closure if hasattr(state, 'closure') else state
            for item in items:
                # Extract core text "A->alpha.beta"
                # generator_clr.Item.__new__ stores the string.
                # item is the string.
                # However, iterating 'item' yields characters.
                # We can't trust str(item) because it appends lookaheads.
                # But we know `item` is a str subclass.
                # Item slicing `item[:]` works to extract characters.
                core_text = "".join(list(item))
                
                for la in item.lookahead:
                    core_map[core_text].add(la)
                    
        # Create new Items with merged lookaheads
        for core, lookaheads in core_map.items():
            new_item = generator_clr.Item(core, list(lookaheads))
            self.closure.append(new_item)

def calc_states_lalr():
    # 1. Get CLR states (which are processed by generator_clr.calc_states)
    # Note: generator_clr.calc_states might already return State objects or lists
    clr_raw = generator_clr.calc_states()
    
    # Standardize to State objects
    generator_clr.State._id = 0
    clr_states = []
    for s in clr_raw:
        if not isinstance(s, generator_clr.State):
            clr_states.append(generator_clr.State(s))
        else:
            # Re-id for consistency if already States
            s.no = generator_clr.State._id
            generator_clr.State._id += 1
            clr_states.append(s)
    
    # 3. Group by Core
    states_by_core = defaultdict(list)
    
    for state in clr_states:
        items = state.closure
        
        # Signature: sorted list of core strings
        cores = []
        for item in items:
             # Extract core text "A->alpha.beta"
             # Since it's a generator_clr.Item, str(item) might have lookaheads.
             # We use the list-casting trick or slice to get core text.
             core_text = "".join(list(item))
             cores.append(core_text)
        
        signature = tuple(sorted(cores))
        states_by_core[signature].append(state)
        
    # 4. Create LALR states
    lalr_states = []
    
    for signature, group in states_by_core.items():
        merged_state = LALRState(group)
        lalr_states.append(merged_state)

    # Sort by the first original ID for consistent ordering
    lalr_states.sort(key=lambda s: s.original_ids[0])
    
    return lalr_states

def make_table_lalr(states):
    table = OrderedDict()
    
    # Helper: find LALR state by Core
    def getstateno_lalr(target_closure):
        # target_closure: list of Items
        target_cores = sorted(["".join(list(itm)) for itm in target_closure])
        
        for s in states:
            s_cores = sorted(["".join(list(itm)) for itm in s.closure])
            if target_cores == s_cores:
                return s.no
        return -1

    # Initialize Rows
    for s in states:
        table[s.no] = OrderedDict()
        
    for s in states:
        # CALCULATE ACTIONS
        for item in s.closure:
            head, body = item.split('→')
            symbols = generator_clr.split_body_with_dot(body.strip())
            
            if '.' in symbols and symbols.index('.') < len(symbols) - 1:
                # SHIFT
                dot_pos = symbols.index('.')
                term = symbols[dot_pos + 1]
                
                if term in generator_clr.t_list:
                    # GOTO using CLR check
                    next_closure = generator_clr.goto(s.closure, term)
                    next_id = getstateno_lalr(next_closure)
                    
                    if next_id != -1:
                        action = f"s{next_id}"
                        # Conflict Check
                        if term in table[s.no]:
                             prev = table[s.no][term]
                             # Only add if distinct
                             if str(action) != str(prev) and action not in prev:
                                 if isinstance(prev, set):
                                     prev.add(action)
                                 else:
                                     table[s.no][term] = {prev, action}
                        else:
                             table[s.no][term] = action

            elif '.' in symbols and symbols.index('.') == len(symbols) - 1:
                 # REDUCE
                 if head == list(firstandfollows.nt_list.keys())[0]: # Start Symbol
                     for la in item.lookahead:
                         if la == '$':
                             table[s.no]['$'] = "Aceptar"
                 else:
                     prod_no = generator_clr.getprodno(item)
                     for la in item.lookahead:
                         action = f"r{prod_no}"
                         if la in table[s.no]:
                             prev = table[s.no][la]
                             if str(action) != str(prev) and action not in prev: 
                                 if isinstance(prev, set):
                                     prev.add(action)
                                 else:
                                     table[s.no][la] = {prev, action}
                         else:
                             table[s.no][la] = action
                             
        # CALCULATE GOTO (NTs)
        for nt in generator_clr.nt_list:
            next_closure = generator_clr.goto(s.closure, nt)
            if not next_closure: continue
            
            next_id = getstateno_lalr(next_closure)
            if next_id != -1:
                table[s.no][nt] = str(next_id)

    return table

def format_states(states, codigos_equivalentes={}, show_lambda=False, empty_symbol='λ'):
    # Reuse generator_clr formatter, but handle LALR State ID (string) if needed
    # generator_clr.format_states uses enumerate idx for ID.
    # LALR states have custom IDs (s.no). 
    # We should override or wrap it.
    
    output = []
    for s in states:
        output.append(f"State {s.no}:")
        
        items = s.closure
        for item in items:
            item_str = item.replace('.', '●').replace('→', '->')
            if codigos_equivalentes:
                for cod, txt in codigos_equivalentes.items():
                    item_str = item_str.replace(cod, txt)
            
            # Lambda/Epsilon
            if "->" in item_str:
                lhs, rhs = item_str.split("->", 1)
                for bad in ['λ', 'ε']: rhs = rhs.replace(bad, "")
                if rhs.replace('●', '').strip() == "":
                    if show_lambda:
                        if rhs.strip().startswith('●'): rhs = f"● {empty_symbol}"
                        else: rhs = f"{empty_symbol} ●"
                item_str = f"{lhs}-> {rhs}"

            lookaheads = item.lookahead
            for la in lookaheads:
                 la_str = codigos_equivalentes.get(la, la) if codigos_equivalentes else la
                 output.append(f"  [ {item_str}, {la_str} ]")
        output.append("")
    return "\n".join(output)

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
import textwrap

def export_items_to_pdf(states, filename="states_lalr1.pdf", show_lambda=False, empty_symbol='λ', codigos_equivalentes={}):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    margin = inch
    y = height - margin

    c.setFont("Times-Roman", 12)

    for state in states:
        # Use state.no (e.g. "36")
        titulo = f"Item{state.no}{{"
        
        if y < margin:
            c.showPage()
            c.setFont("Times-Roman", 12)
            y = height - margin
            
        c.drawString(margin, y, titulo)
        y -= 16
        
        items = state.closure
        for item in items:
            item_str = item.replace('.', '●').replace('→', '->')
            if codigos_equivalentes:
                for cod, txt in codigos_equivalentes.items():
                    item_str = item_str.replace(cod, txt)
            
            if "->" in item_str:
                lhs, rhs = item_str.split("->", 1)
                for bad in ['λ', 'ε']: rhs = rhs.replace(bad, "")
                if rhs.replace('●', '').strip() == "":
                    if show_lambda:
                        if rhs.strip().startswith('●'): rhs = f"● {empty_symbol}"
                        else: rhs = f"{empty_symbol} ●"
                item_str = f"{lhs}-> {rhs}"

            for la in item.lookahead:
                la_str = codigos_equivalentes.get(la, la) if codigos_equivalentes else la
                line = f"[ {item_str}, {la_str} ]"

                wrapped_lines = textwrap.wrap(line, width=90)
                for wrapped_line in wrapped_lines:
                    if y < margin:
                        c.showPage()
                        c.setFont("Times-Roman", 12)
                        y = height - margin
                    c.drawString(margin, y, wrapped_line)
                    y -= 14

        if y < margin:
            c.showPage()
            c.setFont("Times-Roman", 12)
            y = height - margin
        c.drawString(margin, y, "}")
        y -= 20

    c.save()
    print(f"✅ PDF generado: {filename}")

