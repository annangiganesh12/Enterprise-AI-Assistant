

from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:

    """
    Perform mathematical calculations.
    Use this tool when an exact numerical calculation is required.
    """

    try:

        result = eval(
            expression,
            {"__builtins__":{}},{}
        )

        return str(result)

    except Exception:
        return "Unable to calculate the expression."