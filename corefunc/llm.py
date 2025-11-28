# core/llm.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st

llm = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"],
    model="openai/gpt-3.5-turbo",  # fastree, cheap, excellent Kiswahili
    temperature=0.3,
)

prompt_en = ChatPromptTemplate.from_template(
    """You are an expert in simplifying Kenyan laws for ordinary citizens.
Explain this bill in very simple, everyday English that a Form 4 leaver can understand.
Use short sentences. Use examples where possible. Avoid legal jargon or explain it immediately.
Focus on: What problem does this bill solve? Who does it affect? What changes will happen if it passes?

Bill text:
{text}
"""
)

prompt_sw = ChatPromptTemplate.from_template(
    """Wewe ni mtaalamu wa kurahisisha sheria za Kenya kwa wananchi wa kawaida.
Eleza muswada huu kwa Kiswahili rahisi sana ambacho mwanafunzi wa Kidato cha 4 anaweza kuelewa.
Tumia sentensi fupi. Toa mifano inapowezekana. Epuka maneno magumu ya sheria au yaeleze mara moja.
Zingatia: Muswada huu unatatua tatizo gani? Unawahusu nani? Mabadiliko gani yatatokea kama utapitishwa?

Maandishi ya muswada:
{text}
"""
)

chain_en = prompt_en | llm
chain_sw = prompt_sw | llm


@st.cache_data(ttl=3600)
def generate_summary(bill_text: str, lang: str = "English") -> str:
    if not bill_text or len(bill_text) < 100:
        return "Sorry, not enough text was extracted from this bill to summarize."

    text = bill_text[
        :15000
    ]  # Gemini Flash handles up to 1M tokens, but we keep it fast

    try:
        if lang == "Kiswahili":
            result = chain_sw.invoke({"text": text})
        else:
            result = chain_en.invoke({"text": text})
        return result.content
    except Exception as e:
        return f"Summary failed: {str(e)}"
