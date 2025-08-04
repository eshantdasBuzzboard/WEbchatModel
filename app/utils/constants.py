# Action to question mapping
ACTION_QUESTIONS = {
    "rewrite-clarity": """
Rewrite this content to maximize clarity.
• Do not add, remove, or invent any information, examples, or details not present in the original text.
• Only rephrase to improve clarity, structure, and readability.
• Do not elaborate, summarize, or shorten the content beyond what is necessary for clarity.
• The output must remain within 10 percent of the original word count.
• Do not repeat any information.
• Preserve all original meaning, intent, and detail.

""",
    "simplify-language": """
Rewrite this content using simpler language and straightforward sentence structures.
• Do not add, remove, or invent any information, examples, or details not present in the original text.
• Only change words and sentences to make them easier to understand, and to clarify the meaning.
• Do not elaborate, summarize, or shorten the content beyond what is necessary for simplicity.
• The output must remain within 10 percent of the original word count.
• Do not repeat any information.
• Preserve all original meaning, intent, and detail.

""",
    "make-human": """
Rewrite this content so it sounds natural, conversational, and exactly human-like, using an engaging tone.
• Do not add, remove, or invent any information, examples, or details not present in the original text.
• Only rephrase sentences and adjust tone to sound more like natural human webpage expert writing.
• Do not elaborate, summarize, or shorten the content beyond what is necessary for a natural flow.
• The output must remain within 10 percent of the original word count.
• Do not repeat any information.
• Preserve all original meaning, intent, and detail.

""",
    "bullet-points": """
Convert this content into clear, concise bullet points.
• Do not invent any information, examples, or details not present in the original text.
• Break down the existing information into logical, easy-to-read bullet points without repeating anything.
• Keep all original meaning and details.
• The total output must remain within 10 percent of the original word count.
• Preserve the original intent, detail, and factual accuracy.

""",
    "smaller-paragraphs": """
Rewrite this content by dividing it into smaller, easy-to-read paragraphs.
• Do not invent any information, examples, or details not present in the original text.
• Only break up long paragraphs into shorter ones for better readability.
• Do not summarize, expand, or repeat content; retain all original meaning and details.
• The total output must remain within 10 percent of the original word count.
• Preserve the original intent, detail, and factual accuracy.

""",
    "shorten": """
Shorten this content while preserving all essential meaning, intent, and factual details.
• Aggressively remove all unnecessary words, repetitive phrases, and filler sentences.
• Rephrase sentences for maximum conciseness.
• Retain every important fact, data point, or key idea; do not remove any crucial information.
• Do not add, invent, or elaborate on the original content. **Strictly do not break the format of the content.**
• The final output must be 20-30 percent shorter than the original (target a reduction of at least one-fourth).
• Do not repeat information.

""",
    "fix-grammar": "Fix any grammar and punctuation errors in this text",
}
