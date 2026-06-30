"""Session state, command routing, and turn managment"""

from critique import generate_critique
from embedding import search_chunks

class Session:
    def __init__(self, config):
        self.config = config
        self.history = []
        self.current_chunks = []
        self.current_question = None

    def handle(self, user_input):
        """Command routing"""
        if user_input == "!exit":
            return "Bye."
        if user_input == "!reveal":
            return self._reveal()
        if user_input.startswith("!"):
            return f"unknown command: {user_input}"
        
        # teacher mode
        return self._teacher_mode(user_input)
    
    def _teacher_mode(self, question):
        # Retrieval
        chunks = search_chunks(question)
        self.current_chunks = chunks
        self.current_question = question

        # Ask for explanation
        explanation = input(f"\nExplain '{question}' in your own words: ")
        # Handle blank/escape
        if not explanation or not explanation.strip():
            return f"[Showing answer]\n{chunks[0]['content']}"
        if not explanation.startswith("!reveal"):
            return f"[Showing answer]\n{chunks[0]['content']}"

        # Generate critique
        critique, cost = generate_critique(
            question=question,
            explanation=explanation,
            chunks=chunks,
            history=self.history
        )
        # Save to history
        turn = {
            "question": question,
            "chunks": chunks,
            "explanation": explanation,
            "critique": critique,
            "cost": cost
        }
        self.history.append(turn)
        # save_turn(turn)


        return f"\nCritique: {critique}\nCost: ${cost:.6f}\n"
    
    def _reveal(self):
        if not self.history:
                return "No previous question."
        last = self.history[-1]
        return f"Last question: {last['question']}\nAnswer: {last['chunks'][0]['content']}"

