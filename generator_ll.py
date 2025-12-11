from collections import defaultdict
import primerosysiguientes

LAMBDA = primerosysiguientes.LAMBDA 

def compute_ll1_table():
    """
    Computes the LL(1) parsing table using the global state in `primerosysiguientes`.
    Returns:
        dict: A dictionary representing the table {NonTerminal: {Terminal: ProductionIndex}}.
    """
    tabla = defaultdict(dict)

    for i, prod in enumerate(primerosysiguientes.production_list):
        head, body = prod.split("→")
        head = head.strip()
        body_syms = body.strip().split()

        # Calculate First(body)
        first = primerosysiguientes.compute_first_sequence(body_syms)

        # Rule 1: For each terminal 'a' in First(beta), add A->beta to M[A, a]
        for t in first - {LAMBDA}:
            tabla[head][t] = i

        # Rule 2: If epsilon in First(beta), add A->beta to M[A, b] for each b in Follow(A)
        # Also, if epsilon in First(beta) and $ in Follow(A), add A->beta to M[A, $]
        if LAMBDA in first:
            follow = primerosysiguientes.get_follow(head)
            for f in follow:
                tabla[head][f] = i

    return dict(tabla)

class TreeNode:
    def __init__(self, label, children=None):
        self.label = label
        self.children = children if children else []

    def to_dict(self):
        return {
            "name": self.label,
            "children": [c.to_dict() for c in self.children]
        }

    def __repr__(self):
        return f"{self.label}"

def parse_input(table, start_symbol, input_tokens):
    """
    Parses input and returns:
    1. Parse Tree (root node) or Error String.
    2. List of steps (dictionaries) for visualization table:
       [{'stack': ..., 'input': ..., 'action': ...}, ...]
    """
    tokens = input_tokens + ['$']
    stack = ['$', start_symbol]
    
    if start_symbol not in primerosysiguientes.nt_list:
        return f"Error: Start symbol '{start_symbol}' not found.", []

    root = TreeNode(start_symbol)
    stack_nodes = [None, root] # Parallel stack for tree nodes
    
    cursor = 0
    steps = [] 
    
    while len(stack) > 0:
        top = stack[-1]
        current_node = stack_nodes[-1]
        current_token = tokens[cursor]
        input_view = " ".join(tokens[cursor:])
        stack_view = " ".join(stack[::-1]) # Reverse stack for display ($ on left)
        
        step_entry = {
            "stack": stack_view,
            "input": input_view,
            "action": ""
        }
        
        if top == '$':
            if current_token == '$':
                step_entry["action"] = "Accept"
                steps.append(step_entry)
                return root, steps
            else:
                return f"Error: Unexpected input at end.", steps
        
        if top == current_token:
            # Match
            step_entry["action"] = f"Match {top}"
            stack.pop()
            stack_nodes.pop()
            cursor += 1
        elif top in primerosysiguientes.t_list or top == '$':
             return f"Error: Expected '{top}', found '{current_token}'", steps
        elif top in primerosysiguientes.nt_list:
            if current_token not in table.get(top, {}):
                return f"Error: No rule for [{top}, {current_token}]", steps
            
            prod_idx = table[top][current_token]
            prod = primerosysiguientes.production_list[prod_idx]
            
            step_entry["action"] = f"{prod}" # Simplified action: just the production
            
            head, body = prod.split("→")
            body_syms = body.strip().split()
            
            stack.pop()
            stack_nodes.pop()
            
            children = []
            if body_syms == [LAMBDA]:
                child = TreeNode(LAMBDA)
                children.append(child)
            else:
                for sym in body_syms:
                    children.append(TreeNode(sym))
            
            current_node.children = children
            
            if body_syms != [LAMBDA]:
                for i in range(len(body_syms) - 1, -1, -1):
                    stack.append(body_syms[i])
                    stack_nodes.append(children[i])
        else:
             return f"Error: Unknown symbol '{top}'", steps
             
        steps.append(step_entry)
             
    return root, steps
