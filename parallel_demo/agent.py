from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

MODEL = "gemini-3.8-flash"

style_agent = LlmAgent(
    name="style_agent",
    model=MODEL,
    instruction="Review the code in the user's message for STYLE issues only. Max 3 bullet points.",
    output_key="style_review",
)

bug_agent = LlmAgent(
    name="bug_agent",
    model=MODEL,
    instruction="Review the code in the user's message for BUGS only. Max 3 bullet points.",
    output_key="bug_review",
)

security_agent = LlmAgent(
    name="security_agent",
    model=MODEL,
    instruction="Review the code in the user's message for SECURITY issues only. Max 3 bullet points.",
    output_key="security_review",
)

parallel_reviews = ParallelAgent(
    name="parallel_reviews",
    sub_agents=[style_agent, bug_agent, security_agent],
)

summarizer = LlmAgent(
    name="summarizer",
    model=MODEL,
    instruction="""Combine the three reviews below into one short final review.
Group it under: Bugs, Security, Style. Remove duplicates.

Style review: {style_review}
Bug review: {bug_review}
Security review: {security_review}""",
)

root_agent = SequentialAgent(
    name="review_pipeline",
    sub_agents=[parallel_reviews, summarizer],
)