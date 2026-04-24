# ============================================================
# backend/services/llm_service.py — Groq LLM Wrapper (FREE API)
# ============================================================

import json
from typing import List
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

# Groq uses the OpenAI-compatible SDK — just point to a different base_url
from openai import OpenAI, RateLimitError, AuthenticationError, APIConnectionError

from backend.config import settings


class LLMService:
    """
    LLM wrapper using Groq's free API (OpenAI-compatible interface).

    Groq provides:
    - llama-3.3-70b-versatile  ← best quality, use this
    - llama3-8b-8192           ← faster/cheaper fallback
    - mixtral-8x7b-32768       ← large context window

    The OpenAI SDK works with Groq by just changing base_url + api_key.
    No new package needed — groq IS openai-compatible.
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = "llama-3.3-70b-versatile"   # Best free Groq model
        self.fallback_model = "llama3-8b-8192"    # Faster fallback
        self.max_tokens = 2000

    # ──────────────────────────────────────────────────
    # Core Chat Method
    # ──────────────────────────────────────────────────

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def chat(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = None,
    ) -> str:
        """
        Send a chat request to Groq API (OpenAI-compatible).
        Returns the response text string.
        """
        max_tokens = max_tokens or self.max_tokens

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            answer = response.choices[0].message.content.strip()
            usage = response.usage
            logger.debug(
                f"Groq LLM [{self.model}]: "
                f"{usage.prompt_tokens} prompt + {usage.completion_tokens} completion tokens"
            )
            return answer

        except AuthenticationError:
            raise ValueError(
                "Groq API key is invalid. "
                "Check your GROQ_API_KEY in .env — get a free key at https://console.groq.com"
            )
        except RateLimitError:
            logger.warning("Groq rate limit hit — retrying...")
            raise
        except APIConnectionError:
            raise RuntimeError(
                "Cannot connect to Groq API. Check your internet connection."
            )
        except Exception as e:
            # Try fallback model on any other error
            logger.warning(f"Primary model failed ({e}), trying fallback: {self.fallback_model}")
            try:
                response = self.client.chat.completions.create(
                    model=self.fallback_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content.strip()
            except Exception as e2:
                raise RuntimeError(f"LLM request failed on both models: {e2}")

    # ──────────────────────────────────────────────────
    # RAG Q&A
    # ──────────────────────────────────────────────────

    def answer_question(self, question: str, context_chunks: List[str]) -> str:
        """Generate an answer using retrieved context chunks."""
        context = "\n\n---\n\n".join(context_chunks)

        system_prompt = """You are StudyMate AI, an expert academic assistant.
Answer questions based ONLY on the provided context.
Rules:
- Be accurate and concise
- If the answer is not in the context, say: "I couldn't find this in the provided materials."
- Cite page numbers or timestamps when visible in the context
- Use a clear, helpful, educational tone"""

        user_message = f"""CONTEXT:
{context}

QUESTION: {question}

Provide a clear, accurate answer based on the context above."""

        return self.chat(system_prompt, user_message, temperature=0.2)

    # ──────────────────────────────────────────────────
    # Summarization
    # ──────────────────────────────────────────────────

    def summarize(self, text: str, style: str = "bullets", title: str = "") -> str:
        """
        Summarize content in different styles.
        style: 'short' | 'bullets' | 'detailed'
        """
        style_instructions = {
            "short": "Write a 2-3 sentence summary capturing the key idea.",
            "bullets": (
                "Write a structured summary with:\n"
                "- A 1-sentence overview at the top\n"
                "- 4-6 key bullet points (1-2 sentences each)\n"
                "- Use markdown bullet format"
            ),
            "detailed": (
                "Write a comprehensive summary including:\n"
                "1. Overview (2-3 sentences)\n"
                "2. Main Topics (detailed paragraphs for each)\n"
                "3. Key Takeaways (bullet list)\n"
                "4. Important Terms/Concepts (if any)"
            ),
        }

        system_prompt = f"""You are StudyMate AI, a world-class academic summarizer.
Create clear, educational summaries that help students understand and retain information.
{style_instructions.get(style, style_instructions['bullets'])}"""

        # Limit to 6000 chars to stay within Groq context limits
        text_snippet = text[:6000]
        title_part = f' titled "{title}"' if title else ""

        user_message = f"""Please summarize the following content{title_part}:

{text_snippet}"""

        return self.chat(system_prompt, user_message, temperature=0.4, max_tokens=1500)

    # ──────────────────────────────────────────────────
    # Quiz Generation
    # ──────────────────────────────────────────────────

    def generate_quiz(
        self, text: str, num_questions: int = 5, difficulty: str = "medium"
    ) -> List[dict]:
        """
        Generate MCQ quiz questions from content.
        Returns list of question dicts.
        """
        system_prompt = """You are StudyMate AI, an expert quiz generator.
Generate multiple-choice questions that test genuine comprehension, not trivia.
CRITICAL: Respond ONLY with valid JSON. No preamble, no markdown code blocks, no explanation."""

        user_message = f"""Generate {num_questions} multiple-choice questions at {difficulty} difficulty from this content.

CONTENT:
{text[:5000]}

Respond with ONLY this exact JSON structure (no markdown, no extra text):
{{
  "questions": [
    {{
      "question_number": 1,
      "question": "Question text here?",
      "options": [
        {{"label": "A", "text": "Option A text"}},
        {{"label": "B", "text": "Option B text"}},
        {{"label": "C", "text": "Option C text"}},
        {{"label": "D", "text": "Option D text"}}
      ],
      "correct_answer": "A",
      "explanation": "Brief explanation of why A is correct."
    }}
  ]
}}"""

        raw = self.chat(system_prompt, user_message, temperature=0.5, max_tokens=2000)

        # Parse JSON — strip any accidental markdown fences
        try:
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            data = json.loads(raw)
            return data.get("questions", [])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quiz JSON: {e}\nRaw response:\n{raw[:600]}")
            raise ValueError(
                "The AI returned malformed quiz data. Please try again."
            )

    # ──────────────────────────────────────────────────
    # Study Plan (My Addition)
    # ──────────────────────────────────────────────────

    def generate_study_plan(self, summary: str, title: str) -> str:
        """
        Generate a personalized 3-day study plan from a content summary.
        """
        system_prompt = """You are StudyMate AI, a personal academic coach.
Based on content summaries, you create actionable, time-blocked study plans that are practical and motivating."""

        user_message = f"""Create a 3-day study plan for mastering this topic: "{title}"

CONTENT SUMMARY:
{summary}

Format the plan as:
## Day 1 — Foundation
(concepts to cover, estimated time, activities)

## Day 2 — Deep Dive
(deeper topics, practice exercises, estimated time)

## Day 3 — Review & Test Yourself
(review strategy, self-test tips, estimated time)

## Recommended Techniques
(2-3 study techniques suited to this material)

Keep it practical, specific, and motivating. Use markdown formatting."""

        return self.chat(system_prompt, user_message, temperature=0.6, max_tokens=1200)

    # ──────────────────────────────────────────────────
    # ELI5 Concept Explainer (My Addition)
    # ──────────────────────────────────────────────────

    def explain_concept(self, concept: str, context: str) -> str:
        """
        Explain a concept simply using analogies and examples.
        """
        system_prompt = """You are StudyMate AI. Explain concepts clearly using:
- Simple everyday analogies
- Real-world examples
- Step-by-step breakdowns
Make it understandable for a curious high school student."""

        user_message = f"""Explain the concept: "{concept}"

Context from study materials:
{context[:2000]}"""

        return self.chat(system_prompt, user_message, temperature=0.5)

    # ──────────────────────────────────────────────────
    # Status Check
    # ──────────────────────────────────────────────────

    def is_configured(self) -> bool:
        """Check if Groq API key is properly set."""
        return (
            bool(settings.groq_api_key)
            and settings.groq_api_key != "gsk_placeholder"
            and settings.groq_api_key.startswith("gsk_")
        )
