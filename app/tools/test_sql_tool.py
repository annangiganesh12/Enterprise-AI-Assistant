

from app.tools.sql_tool import sql_tool


questions = [
    "How many employees are in the AI department?",
    "Who joined the company after 2025?",
    "How many leaves has Rahul taken?",
    "Which department has the most employees?",
    "What is the total sales revenue?",
    "Which customer has spent the most money?",
    "What is the total sales for each product?",
]


for question in questions:

    print("\n" + "=" * 60)
    print("QUESTION:", question)

    try:
        result = sql_tool(question)

        print("RESULT:")
        print(result["results"])

        print("ANSWER:\n")
        print(result["answer"])

    except Exception as e:
        print("ERROR:", e)