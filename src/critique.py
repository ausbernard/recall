"""All LLM calls. Single entry point: generate_critique()."""

from anthropic import Anthropic
from src.config import get_api_key, get_model, get_temperature

def _add_line_numbers(code):
    lines = code.strip().split('\n')
    numbered = []
    for i, line in enumerate(lines, 1):
        numbered.append(f"{i:3d} | {line}")
    
    return '\n'.join(numbered)

def call_claude(prompt, model=get_model()):
    client = Anthropic(
        api_key=get_api_key()
    )
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=get_temperature(),  # Deterministic output - This makes the model less creative and more consistent. But it also makes it more rigid. It won't explore nuance as well.
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

