# Generador de Parsers (Analizadores Sintácticos)

[![English](https://img.shields.io/badge/Read_in-English-blue.svg)](README.md)

Este proyecto es una herramienta interactiva diseñada para la creación, visualización y simulación de gramáticas utilizando diversos algoritmos de análisis sintáctico. Desarrollado como parte del curso de Lenguajes y Compiladores, permite a los usuarios definir gramáticas y obtener tablas de análisis, conjuntos de Primero y Siguiente, y simulaciones de derivación en tiempo real.

## Algoritmos Soportados

El generador incluye soporte completo para los siguientes algoritmos de análisis sintáctico (Bottom-Up y Top-Down):

- **LL(1)**: Análisis descendente predecible.
- **LR(0)**: Análisis ascendente con estados de cierre canónico.
- **SLR(1)**: Análisis ascendente simple con conjuntos de Siguiente.
- **CLR(1)**: Análisis ascendente canónico con símbolos de anticipación (lookahead).
- **LALR(1)**: Análisis ascendente con fusión de estados de núcleo idéntico.

## Características Principales

- **Interfaz Gráfica (GUI)**: Diseñada con PyQt6 para una experiencia de usuario fluida e intuitiva.
- **Cálculo de Conjuntos**: Generación automática de los conjuntos **Primero (First)** y **Siguiente (Follow)**.
- **Visualización de Colecciones Canónicas**: Visualización detallada de los estados y sus ítems.
- **Simulación de Análisis**: Herramienta interactiva para probar cadenas de entrada y visualizar los pasos del stack (pila).
- **Exportación de Datos**:
    - Tablas de análisis en formato **CSV**.
    - Reportes de estados y colecciones canónicas en **PDF**.
- **Manejo de Símbolos Especiales**: Soporte nativo para símbolos de producción vacía (λ / ε).

![Ejemplo del Generador de Parsers](https://github.com/JimSegovia/ParserGenerator/blob/main/assets/example.png?raw=true)

## Requisitos del Sistema

Para ejecutar este proyecto, necesitarás:

- **Python 3.8+**
- **PyQt6**: Para la interfaz gráfica.
- **ReportLab**: Necesario para la exportación de reportes en PDF.

## Instalación y Ejecución

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/JimSegovia/ParserGenerator.git
    cd ParserGenerator
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install PyQt6 reportlab
    ```

3.  **Ejecutar la aplicación:**
    ```bash
    python pargen_gui.py
    ```

## Guía de Uso

1.  **Definir la Gramática**:
    - Ingrese los **No Terminales** separados por `|` (ej: `S|A|B`).
    - Ingrese los **Terminales** separados por `|` (ej: `id|+|*|(|)`).
    - Defina las **Reglas de Producción** (una por línea, usando `->` o `→`).
2.  **Seleccionar Algoritmo**: Use el menú desplegable para elegir entre LL(1), LR(0), SLR(1), CLR(1) o LALR(1).
3.  **Generar Parser**: Haga clic en el botón verde **"Build Parser"**.
4.  **Analizar Cadenas**: En la pestaña **"Parse Tree"**, ingrese una cadena de tokens separados por espacios (ej: `id + id`) y presione **"Parse Input"**.

---
**Desarrollado por:** Jim Segovia
