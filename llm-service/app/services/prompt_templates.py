"""Prompt template service for RAG and specialized tasks

Provides system prompts and formatting for various task types in Hindi and English.
"""

import logging
from typing import List, Optional
from app.models.completions import Message

logger = logging.getLogger(__name__)


class PromptTemplateService:
    """Manages prompt templates for different tasks and languages"""

    def __init__(self):
        """Initialize prompt template service"""
        self.templates = self._load_templates()

    def format_messages(self, messages: List[Message]) -> str:
        """Format message list into prompt string for vLLM

        Args:
            messages: Chat message history

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"[SYSTEM]\n{msg.content}\n")
            elif msg.role == "user":
                prompt_parts.append(f"[USER]\n{msg.content}\n")
            elif msg.role == "assistant":
                prompt_parts.append(f"[ASSISTANT]\n{msg.content}\n")

        # Add response prefix
        prompt_parts.append("[ASSISTANT]\n")

        return "".join(prompt_parts)

    def get_qa_system_prompt(self, language: str = "en") -> str:
        """Get system prompt for QA task

        Args:
            language: "hi" for Hindi, "en" for English

        Returns:
            System prompt string
        """
        if language == "hi":
            return self.templates["qa_hindi"]
        else:
            return self.templates["qa_english"]

    def get_summarization_prompt(self, language: str = "en") -> str:
        """Get system prompt for summarization task

        Args:
            language: "hi" for Hindi, "en" for English

        Returns:
            System prompt string
        """
        if language == "hi":
            return self.templates["summarize_hindi"]
        else:
            return self.templates["summarize_english"]

    def get_sentiment_prompt(self) -> str:
        """Get system prompt for sentiment analysis task

        Returns:
            System prompt string
        """
        return self.templates["sentiment"]

    def get_search_summary_prompt(self) -> str:
        """Get system prompt for generating search result summaries

        Returns:
            System prompt string
        """
        return self.templates["search_summary"]

    def _load_templates(self) -> dict:
        """Load prompt templates

        Returns:
            Dictionary of template name -> template text
        """
        return {
            "qa_english": self._qa_english_prompt(),
            "qa_hindi": self._qa_hindi_prompt(),
            "summarize_english": self._summarize_english_prompt(),
            "summarize_hindi": self._summarize_hindi_prompt(),
            "sentiment": self._sentiment_prompt(),
            "search_summary": self._search_summary_prompt()
        }

    @staticmethod
    def _qa_english_prompt() -> str:
        """English QA system prompt"""
        return """You are an expert assistant for the Ministry of Culture, Government of India.
Your role is to provide accurate, factual answers about Indian heritage, culture, monuments,
traditions, and government cultural initiatives.

Important guidelines:
1. Provide answers based ONLY on the provided context. Do not use external knowledge.
2. If the answer is not in the context, clearly state: "I don't have this information."
3. Cite sources when referencing specific facts.
4. Be respectful and inclusive of all cultures and traditions mentioned.
5. Keep responses concise but comprehensive.
6. Use simple language for clarity.

If you cannot find a reliable answer in the provided context, direct the user to contact
the Ministry of Culture helpline at 011-23388261 or email arit-culture@gov.in."""

    @staticmethod
    def _qa_hindi_prompt() -> str:
        """Hindi QA system prompt"""
        return """आप भारत के संस्कृति मंत्रालय के लिए एक विशेषज्ञ सहायक हैं।
आपकी भूमिका भारतीय विरासत, संस्कृति, स्मारकों, परंपराओं और सरकारी सांस्कृतिक पहलों के बारे में
सटीक और तथ्यपूर्ण उत्तर प्रदान करना है।

महत्वपूर्ण दिशानिर्देश:
1. उत्तर केवल दिए गए संदर्भ के आधार पर प्रदान करें। बाहरी ज्ञान का उपयोग न करें।
2. यदि संदर्भ में उत्तर नहीं है, तो स्पष्ट रूप से कहें: "मेरे पास यह जानकारी नहीं है।"
3. विशिष्ट तथ्यों का संदर्भ देते समय स्रोत का उल्लेख करें।
4. सभी संस्कृतियों और परंपराओं के प्रति सम्मानपूर्ण और समावेशी रहें।
5. प्रतिक्रिया को संक्षिप्त लेकिन व्यापक रखें।
6. स्पष्टता के लिए सरल भाषा का उपयोग करें।

यदि आप दिए गए संदर्भ में विश्वसनीय उत्तर नहीं खोज सकते, तो उपयोगकर्ता को
संस्कृति मंत्रालय हेल्पलाइन 011-23388261 पर संपर्क करने या
arit-culture@gov.in पर ईमेल करने के लिए निर्देशित करें।"""

    @staticmethod
    def _summarize_english_prompt() -> str:
        """English summarization prompt"""
        return """You are an expert summarization specialist. Your task is to create
clear, concise summaries of content related to Indian culture and heritage.

Guidelines:
1. Capture the key points accurately and comprehensively
2. Maintain factual accuracy without adding interpretation
3. Use simple, clear language
4. Keep the summary to 2-3 sentences for short content, 3-5 for longer content
5. Preserve important details about dates, names, and statistics
6. Highlight the cultural or historical significance when relevant"""

    @staticmethod
    def _summarize_hindi_prompt() -> str:
        """Hindi summarization prompt"""
        return """आप एक विशेषज्ञ सारांशकार हैं। आपका कार्य भारतीय संस्कृति और विरासत से संबंधित
सामग्री के स्पष्ट, संक्षिप्त सारांश बनाना है।

दिशानिर्देश:
1. मुख्य बिंदुओं को सटीकता से और व्यापक रूप से कैप्चर करें
2. बिना व्याख्या जोड़े तथ्यात्मक सटीकता बनाए रखें
3. सरल, स्पष्ट भाषा का उपयोग करें
4. छोटी सामग्री के लिए सारांश को 2-3 वाक्यों तक रखें, लंबी सामग्री के लिए 3-5
5. तारीखों, नामों और सांख्यिकी के बारे में महत्वपूर्ण विवरण संरक्षित करें
6. जब प्रासंगिक हो तो सांस्कृतिक या ऐतिहासिक महत्व को हाइलाइट करें"""

    @staticmethod
    def _sentiment_prompt() -> str:
        """Sentiment analysis prompt"""
        return """Analyze the sentiment of the given text and classify it as:
- POSITIVE: Expressing approval, satisfaction, or positive emotions
- NEGATIVE: Expressing disapproval, dissatisfaction, or negative emotions
- NEUTRAL: Factual or objective statements without clear sentiment
- MIXED: Containing both positive and negative sentiments

Provide a brief explanation of the sentiment and identify key sentiment-bearing words."""

    @staticmethod
    def _search_summary_prompt() -> str:
        """Search result AI summary prompt"""
        return """You are an expert at creating concise, informative summaries of search results.
Generate a 2-3 sentence summary that:
1. Captures the main topic and relevance
2. Highlights key information the user is likely seeking
3. Maintains factual accuracy
4. Uses clear, accessible language
5. Includes relevant cultural or historical context if applicable"""
