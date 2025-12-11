
import sys
import io
import importlib.util
from collections import OrderedDict
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QLabel, QLineEdit, 
                             QPlainTextEdit, QPushButton, QTabWidget, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QFrame, QMessageBox, QListWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

# --- Dynamic Import for "Generador CLR.py" ---
# Because the filename has spaces, we can't do a normal import.
spec = importlib.util.spec_from_file_location("generador_clr", "Generador CLR.py")
generador_clr = importlib.util.module_from_spec(spec)
sys.modules["generador_clr"] = generador_clr
spec.loader.exec_module(generador_clr)

# Import primerosysiguientes (dependency of Generador CLR)
import primerosysiguientes

class GrammarInputPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Definición de la Gramática")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addWidget(QLabel("No Terminales (separados por |):"))
        self.nt_input = QLineEdit()
        self.nt_input.setPlaceholderText("Ej: S|A|B")
        layout.addWidget(self.nt_input)

        layout.addWidget(QLabel("Terminales (separados por |):"))
        self.t_input = QLineEdit()
        self.t_input.setPlaceholderText("Ej: a|b|+|*|id")
        layout.addWidget(self.t_input)

        layout.addWidget(QLabel("Producciones (una por línea, usar '->' o '→'):"))
        self.productions_input = QPlainTextEdit()
        self.productions_input.setFont(QFont("Courier New", 10))
        self.productions_input.setPlaceholderText("S -> A b\nA -> a")
        layout.addWidget(self.productions_input)

        self.build_button = QPushButton("Construir Analizador Sintáctico")
        self.build_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(self.build_button)
        
        self.setLayout(layout)

class ResultsPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Panel de Salida")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        self.tabs = QTabWidget()
        
        self.table_widget = QTableWidget()
        self.tabs.addTab(self.table_widget, "Tabla de Análisis")
        
        self.productions_list = QListWidget()
        self.tabs.addTab(self.productions_list, "Reglas Numeradas")
        
        layout.addWidget(self.tabs)

        self.export_pdf_button = QPushButton("Exportar Reporte PDF")
        self.export_pdf_button.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        layout.addWidget(self.export_pdf_button)

        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador de Analizadores Sintácticos - CLR Generator")
        self.resize(1300, 850)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- Left Area ---
        input_splitter = QSplitter(Qt.Orientation.Vertical)
        
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        
        algo_layout = QHBoxLayout()
        algo_layout.addWidget(QLabel("Algoritmo:"))
        self.algo_selector = QComboBox()
        self.algo_selector.addItems(["LL(1)", "LR(0)", "SLR(1)", "LALR(1)", "CLR(1)"])
        self.algo_selector.setCurrentText("CLR(1)")
        algo_layout.addWidget(self.algo_selector)
        algo_layout.addStretch()
        top_layout.addLayout(algo_layout)
        
        self.grammar_panel = GrammarInputPanel()
        top_layout.addWidget(self.grammar_panel)
        input_splitter.addWidget(top_container)

        # --- Intermediate Results ---
        intermediate_group = QWidget()
        intermediate_layout = QVBoxLayout(intermediate_group)
        intermediate_layout.addWidget(QLabel("Resultados Intermedios"))
        
        self.intermediate_tabs = QTabWidget()
        self.closure_text = QPlainTextEdit()
        self.closure_text.setReadOnly(True)
        self.closure_text.setFont(QFont("Consolas", 10))
        self.intermediate_tabs.addTab(self.closure_text, "Colección Canónica / Closure")
        
        intermediate_layout.addWidget(self.intermediate_tabs)
        input_splitter.addWidget(intermediate_group)

        # --- Right Area ---
        self.results_panel = ResultsPanel()

        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(input_splitter)
        main_splitter.addWidget(self.results_panel)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(main_splitter)

        # Connections
        self.grammar_panel.build_button.clicked.connect(self.build_parser)
        self.results_panel.export_pdf_button.clicked.connect(self.export_pdf)

        # State storage
        self.current_table = None
        self.current_states = None

    def build_parser(self):
        # 1. Input Validation
        nt_text = self.grammar_panel.nt_input.text().strip()
        t_text = self.grammar_panel.t_input.text().strip()
        prod_text = self.grammar_panel.productions_input.toPlainText().strip()

        if not nt_text or not t_text or not prod_text:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return

        # 2. Reset Backend State
        primerosysiguientes.nt_list.clear()
        primerosysiguientes.t_list.clear()
        primerosysiguientes.production_list.clear()
        # Reset specific module lists if they are separate copies (they seem shared via import)
        generador_clr.nt_list = [] # It's a list proxy in that file? No, it's reassigned from ntl.keys()
        
        # 3. Parse Inputs
        # Create Objects for NTs
        nt_symbols = [x.strip() for x in nt_text.split('|') if x.strip()]
        for nt in nt_symbols:
            primerosysiguientes.nt_list[nt] = primerosysiguientes.NonTerminal(nt)

        # Create Objects for Terminals
        t_symbols = [x.strip() for x in t_text.split('|') if x.strip()]
        for t in t_symbols:
            primerosysiguientes.t_list[t] = primerosysiguientes.Terminal(t)

        # Parse Productions
        productions = [line.strip() for line in prod_text.split('\n') if line.strip()]
        primerosysiguientes.production_list = productions # Assign directly to the list

        # 4. Run Logic & Capture Output
        output_capture = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = output_capture

        try:
            # Step A: First & Follow (via main wrapper or direct calls)
            # Replicates lines 382-391 in Generador CLR.py
            print("--- FIRST & FOLLOW ---\n")
            for nt_name, nt_obj in primerosysiguientes.nt_list.items():
                primerosysiguientes.compute_first(nt_name)
                primerosysiguientes.compute_follow(nt_name)
                print(f"{nt_name}\n\tFirst: {primerosysiguientes.get_first(nt_name)}")
                print(f"\tFollow: {primerosysiguientes.get_follow(nt_name)}\n")

            # Step B: Augment Grammar
            generador_clr.production_list = primerosysiguientes.production_list
            generador_clr.ntl = primerosysiguientes.nt_list
            generador_clr.tl = primerosysiguientes.t_list
            generador_clr.augment_grammar()
            
            # Update lists in generator module
            generador_clr.nt_list = list(generador_clr.ntl.keys())
            generador_clr.t_list = list(generador_clr.tl.keys()) + ['$']

            # Step C: Calc States (Canonical Collection)
            print("--- COLECCIÓN CANÓNICA (CLOSURE) ---\n")
            states = generador_clr.calc_states()
            self.current_states = states

            # Print states for the text view
            for idx, state in enumerate(states):
                print(f"Estado {idx}:")
                generador_clr.pretty_print_items(state) # Prints to captured stdout
                print("")

            # Step D: Make Table
            table = generador_clr.make_table(states)
            self.current_table = table

        except Exception as e:
            sys.stdout = original_stdout
            QMessageBox.critical(self, "Error de Ejecución", f"Ocurrió un error al generar el analizador:\n{str(e)}")
            import traceback
            traceback.print_exc()
            return
        finally:
            sys.stdout = original_stdout

        # 5. Update UI
        self.closure_text.setPlainText(output_capture.getvalue())
        self.update_results_table(table)
        self.update_productions_list(generador_clr.production_list)

        QMessageBox.information(self, "Éxito", "Analizador Generado Correctamente.")

    def update_results_table(self, table):
        self.results_panel.table_widget.clear()
        
        if not table:
            return

        # Collect columns (all terminals + non-terminals that appear in keys)
        # The table is [State][Symbol] -> Action
        
        all_symbols = set()
        for row in table.values():
            all_symbols.update(row.keys())
        
        # Sort symbols: Terminals first, then Non-Terminals, then $
        # Use existing lists to sort
        sorted_cols = sorted(list(all_symbols)) # Simple sort for now
        
        # Create headers
        self.results_panel.table_widget.setColumnCount(len(sorted_cols))
        self.results_panel.table_widget.setHorizontalHeaderLabels(sorted_cols)
        
        self.results_panel.table_widget.setRowCount(len(table))
        self.results_panel.table_widget.setVerticalHeaderLabels([str(k) for k in table.keys()])

        # Populate
        for r_idx, (state_id, row_data) in enumerate(table.items()):
            for c_idx, symbol in enumerate(sorted_cols):
                if symbol in row_data:
                    action = row_data[symbol]
                    # Format set actions (conflicts) or single strings
                    if isinstance(action, set):
                        text = "/".join(sorted(action))
                        item = QTableWidgetItem(text)
                        item.setBackground(QColor(255, 200, 200)) # Reddish for conflicts
                    else:
                        text = str(action)
                        item = QTableWidgetItem(text)
                        
                        # Color coding
                        if text == "Aceptar":
                            item.setBackground(QColor(200, 255, 200)) # Green
                        elif text.startswith('r'):
                            item.setBackground(QColor(220, 230, 255)) # Light Blue
                    
                    self.results_panel.table_widget.setItem(r_idx, c_idx, item)

        self.results_panel.table_widget.resizeColumnsToContents()

    def update_productions_list(self, prods):
        self.results_panel.productions_list.clear()
        for idx, p in enumerate(prods):
            self.results_panel.productions_list.addItem(f"{idx}: {p}")

    def export_pdf(self):
        if not self.current_states:
             QMessageBox.warning(self, "Aviso", "Primero debe generar el analizador.")
             return
        
        try:
            # We call the existing export function, but we might need to suppress print or ensure it works
            generador_clr.export_items_to_pdf(self.current_states, {}, filename="reporte_clr.pdf")
            QMessageBox.information(self, "PDF Generado", "Se ha generado 'reporte_clr.pdf' exitosamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error PDF", f"Error al generar PDF:\n{str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
