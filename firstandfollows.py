from re import *  # Expresiones regulares
from collections import OrderedDict  # Diccionario ordenado para mantener el orden de inserción

# ------------------------------------------------------------------

class Terminal:  # Representa a un simbolo terminal

    def __init__(self, symbol):
        self.symbol = symbol

    def __str__(self):
        return self.symbol


# ------------------------------------------------------------------

class NonTerminal:  # Representa a un simbolo no terminal

    def __init__(self, symbol):
        self.symbol = symbol
        self.primero = set()
        self.siguiente = set()

    def __str__(self):
        return self.symbol

    def add_primero(self, symbols): self.primero |= set(symbols)  # conjunto primero del no terminal

    def add_siguiente(self, symbols): self.siguiente |= set(symbols)  # conjunto siguiente del no terminal

# ------------------------------------------------------------------

LAMBDA = 'λ'

t_list = OrderedDict()

nt_list = OrderedDict()

production_list = []  # Lista de producciones

# ------------------------------------------------------------------

def compute_all_primeros():
    global production_list, nt_list, t_list

    changed = True
    while changed:
        changed = False
        for prod in production_list:
            head, body = prod.split('→')
            head = head.strip()
            body_syms = body.strip().split()

            if body == '':
                body_syms = [LAMBDA]

            all_nullable = True
            for sym in body_syms:
                # Terminal o símbolo especial
                if sym in t_list or sym == '$':
                    if sym not in nt_list[head].primero:
                        nt_list[head].primero.add(sym)
                        changed = True
                    all_nullable = False
                    break
                elif sym == LAMBDA:
                    if LAMBDA not in nt_list[head].primero:
                        nt_list[head].primero.add(LAMBDA)
                        changed = True
                    all_nullable = False
                    break
                else:
                    # NonTerminal
                    if sym not in nt_list:
                        continue
                        
                    before = len(nt_list[head].primero)
                    nt_list[head].primero |= (nt_list[sym].primero - {LAMBDA})
                    if len(nt_list[head].primero) > before:
                        changed = True

                    if LAMBDA in nt_list[sym].primero:
                        continue
                    else:
                        all_nullable = False
                        break

            if all_nullable:
                if LAMBDA not in nt_list[head].primero:
                    nt_list[head].primero.add(LAMBDA)
                    changed = True

def compute_primero(symbol=None):
    # Wrapper triggering global calculation
    compute_all_primeros()

    # Si se llamó con un símbolo específico (modo wrapper)
    if symbol:
        if symbol in t_list or symbol == '$':
            return {symbol}
        elif symbol in nt_list:
            return nt_list[symbol].primero
        else:
            return set()


def compute_all_siguientes():
    global production_list, nt_list, t_list
    
    # Initialize Start Symbol Follow if empty (or always ensure it has $)
    if not nt_list:
        return

    start_symbol = list(nt_list.keys())[0]
    nt_list[start_symbol].add_siguiente({'$'})

    changed = True
    while changed:
        changed = False
        
        for prod in production_list:
            head, body = prod.split('→')
            head = head.strip()
            body_tokens = body.strip().split()

            for i, B in enumerate(body_tokens):
                if B not in nt_list:
                    continue

                # Case A → α B β
                # Follow(B) += First(β) - {λ}
                
                # Calculate First(β)
                beta = body_tokens[i + 1:]
                first_beta = compute_first_sequence(beta)
                
                before_len = len(nt_list[B].siguiente)
                
                nt_list[B].add_siguiente(first_beta - {LAMBDA})
                
                # If β is nullable (λ in First(β)) or β is empty (end of production)
                # Follow(B) += Follow(head)
                if not beta or LAMBDA in first_beta:
                    current_head_follow = nt_list[head].siguiente
                    if not nt_list[B].siguiente.issuperset(current_head_follow):
                         nt_list[B].add_siguiente(current_head_follow)
                    
                if len(nt_list[B].siguiente) > before_len:
                    changed = True

def compute_siguiente(symbol):
    compute_all_siguientes()
    if symbol in nt_list:
        return nt_list[symbol].siguiente
    return set()

# ------------------------------------------------------------------

def get_primero(symbol):  # wrapper method
    return compute_primero(symbol)

def get_siguiente(symbol):
    global nt_list, t_list
    if symbol in t_list.keys():
        return None
    return nt_list[symbol].siguiente

# ------------------------------------------------------------------

def compute_first_sequence(symbols):
    result = set()
    for sym in symbols:
        # We assume firsts are already computed globally if we are inside compute_all_siguientes
        if sym in t_list or sym == '$':
            first = {sym}
        elif sym in nt_list:
            first = nt_list[sym].primero
        else:
            first = set() # Unknown symbol
            
        result.update(first - {LAMBDA})
        if LAMBDA not in first:
            break
    else:
        result.add(LAMBDA)
    return result


# ------------------------------------------------------------------
def main(pl=None):
    global production_list, nt_list, t_list

    if pl:
        production_list[:] = pl

        for prod in production_list:
            head, body = prod.split('→')
            head = head.strip()
            body_tokens = body.strip().split()

            # Asegura que el símbolo de la cabeza es un no terminal
            if head not in nt_list:
                nt_list[head] = NonTerminal(head)

            for sym in body_tokens:
                if sym == LAMBDA:
                    continue

                if sym not in nt_list and sym not in t_list:
                    # Si el símbolo aparece por primera vez
                    # Lo consideramos terminal si no ha sido cabeza de producción
                    is_non_terminal = any(sym == p.split('→')[0].strip() for p in production_list)
                    if is_non_terminal:
                        if sym not in nt_list:
                             nt_list[sym] = NonTerminal(sym)
                    else:
                        t_list[sym] = Terminal(sym)
                # Si el símbolo ya existe pero hay conflicto de instanciacion
                elif sym in t_list and t_list[sym] is None:
                    t_list[sym] = Terminal(sym)
                elif sym in nt_list and nt_list[sym] is None:
                    nt_list[sym] = NonTerminal(sym)
                    
        # RUN LOGIC
        compute_all_primeros()
        compute_all_siguientes()

        return pl
    else:
        print("Debe pasarse una lista de producciones como argumento.")

# ------------------------------------------------------------------

if __name__ == '__main__':
    from pprint import pprint
    main()
