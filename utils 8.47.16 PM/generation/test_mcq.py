import asyncio
from mcq_generator import MCQGenerator

async def main():
    generator = MCQGenerator()
    questions = await generator.generate_questions()

    for i, q in enumerate(questions, 1):
        print(f"Question {i}:")
        if isinstance(q, str):
            print(q)
        else:
            print(f"Q: {q.question}")
            print(f"A: {q.A}")
            print(f"B: {q.B}")
            print(f"C: {q.C}")
            print(f"D: {q.D}")
            print(f"Answer: {q.Answer}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
