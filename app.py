import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

###classes###
class Session:
    def __init__(self):
        self.history = []
        self.current_question = None
        self.current_chunks = None
        self.current_api_model_cost = None
    
    def handle(self, cmd):
        if cmd == "!reveal":
            return "reveal"
        elif cmd == "!exit":
            return "break out"
        elif cmd.startswith("!"):
            return "unknown"
        return None
    
    def compare(self, explanation, chunk):
        words_a = set(explanation.lower().split())
        words_b = set(chunk.lower().split())
        overlap = words_a & words_b
        missing = words_b - words_a

        return overlap, missing

###
HARDCODED_CHUNKS = """
async def _execute(
    query: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {settings.railway_token}"}

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.post(
            RAILWAY_API,
            headers=headers,
            json={
                "query": query,
                "variables": variables,
            },
        )

    # Transport layer first — did the request even reach a GraphQL server?
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=_transport_error(response))

    # Now we know it's 200, so the body should be GraphQL-shaped JSON.
    payload = response.json()

    # Application layer — server reached, but it didn't like it.
    if "errors" in payload:
        raise HTTPException(
            status_code=502,
            detail=_graphql_error(payload["errors"]),
        )

    if "data" not in payload or payload["data"] is None:
        raise HTTPException(
            status_code=502,
            detail={"kind": "graphql", "errors": [{"message": "no data in response"}]},
        )

    return payload["data"]
"""

FILTERED = {"def", "async", "return", "the", "like"}

###functions###
def call_claude(prompt, model="claude-haiku-4-5-20251001"):
    client = Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0.0,  # Deterministic output - This makes the model less creative and more consistent. But it also makes it more rigid. It won't explore nuance as well.
        system=[
            {
                "type": "text",
                "text": "You are a Socratic tutor. Do NOT correct the user directly. Instead, ask a single question that exposes the flaw in their reasoning. The question should require them to look at the code and think. Do not give them the answer",
                "cache_control": {"type": "ephemeral"}
            }
        ],
        messages = [{
            "role": "user",
            "content": prompt
        }]
    )
    # calculate cost
    usage = response.usage
    total_input_tokens = usage.input_tokens + usage.cache_creation_input_tokens + usage.cache_read_input_tokens

    # Haiku pricing
    input_cost = total_input_tokens * 0.25 / 1_000_000
    output_cost = usage.output_tokens * 1.25 / 1_000_000

    return {
        "text": response.content[0].text,
        "input_tokens": total_input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_read": usage.cache_read_input_tokens,
        "cache_created": usage.cache_creation_input_tokens,
        "cost": input_cost + output_cost
    }

def generate_critique(question, explanation, chunk, overlap, missing, history):
    context = ""
    if history:
        last = history[-1]
        context =f"""
            Previous turn:
            You asked: {last['question']}
            You explained: {last['explanation']}
            Critique: {last['critique']}
        """

    prompt = context + f"""Now the user asked: {question}
        They explained: {explanation}
        The code says: {chunk}

        The code (with line numbers): {_add_line_numbers(chunk)}

        The user mentioned these key terms from the code: {', '.join(list(overlap)[:5]) if overlap else 'none'}
        They missed these key terms: {', '.join(list(missing)[:10]) if missing else 'none'}

        You are a Socratic tutor. Do NOT correct the user directly. Instead, ask a single question that exposes the flaw in their reasoning. The question should require them to look at the code and think. Do not give them the answer:
        1. What they got right (be specific)
        2. Quotes the user's explanation and corrects it
        3. References specific line numbers from the code
        4. Shows the exact code snippet you're referring to
        5. Ends with one concrete question

        Format your critique like this:
        "**You said:** [quote their words]
        **But look at line X:** [code snippet]
        **What you missed:** [explanation]
        **Question to consider:** [specific question]"
    """

    result = call_claude(prompt)

    return result["text"], result["cost"]

def _add_line_numbers(code):
    lines = code.strip().split('\n')
    numbered = []
    for i, line in enumerate(lines, 1):
        numbered.append(f"{i:3d} | {line}")
    
    return '\n'.join(numbered)

###business logic###
session = Session()

while True:

    try:
        print(":> ", end="", flush=True)
        user_input = input()

        response = session.handle(user_input)

        if response == "reveal":
            if session.history:
                last = session.history[-1]
                print(f"Last question: {last['question']}")
                print(f"Answer (chunk): {last['chunks']}")
            else:
                print("No previous question to reveal.")

            continue
        
        elif response == "unknown":
            print("Unknown command")
            continue

        elif response == "break out":
            print("Bye.")
            break
        
        else:
            # teacher mode
            # store the question
            session.current_question = user_input
            # set the chunks (hardcoded)
            session.current_chunks = HARDCODED_CHUNKS

            # get the users explanation
            explanation = input(f"\nExplain '{session.current_question}' in your own words: ")
            if explanation.startswith("!reveal"):
                # Show the answer directly
                print(session.current_chunks)
                continue

            if not explanation or not explanation.strip():
                print("\n[📝 You skipped explaining. Next time, try to describe what you think first.]")
                print("[Showing answer directly:]\n")
                print(session.current_chunks)
                continue
            else:
                # proceed with comparison
                overlap, missing = session.compare(explanation, session.current_chunks)
                critique, cost = generate_critique(
                    session.current_question, 
                    explanation, 
                    session.current_chunks,
                    overlap,
                    missing,
                    session.history,
                )

                print(f"\nCritique: {critique}\n")
                print(f"This turn cost: ${cost:.6f}\n")

                session.history.append({
                    "question": session.current_question,
                    "chunks": session.current_chunks,
                    "explanation": explanation,
                    "overlap": overlap,
                    "missing": missing,
                    "critique": critique,
                    "cost": cost
                })

    except KeyboardInterrupt:
        print("\n> Bye.", flush=True)
        break
