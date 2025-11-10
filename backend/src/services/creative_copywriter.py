"""
AI-powered creative copywriting service using GPT-4.
"""

from typing import Dict, List, Optional
from openai import OpenAI
import os

from ..models.campaign import Product
from ..utils.ai_utils import parse_json_response


class CreativeCopywriter:
  """Generate optimized marketing copy using GPT-4."""

  # Regional and cultural context mapping
  REGION_CONTEXT = {
    "North America": {
      "style": "Direct, benefit-focused, casual-friendly",
      "values": "convenience, innovation, personal success",
      "languages": ["en-US", "es-MX", "fr-CA"]
    },
    "Europe": {
      "style": "Sophisticated, quality-focused, subtle",
      "values": "craftsmanship, sustainability, heritage",
      "languages": ["en-GB", "de-DE", "fr-FR", "es-ES", "it-IT"]
    },
    "Asia Pacific": {
      "style": "Respectful, community-oriented, innovative",
      "values": "harmony, technology, collective benefit",
      "languages": ["zh-CN", "ja-JP", "ko-KR", "hi-IN"]
    },
    "Latin America": {
      "style": "Warm, passionate, family-oriented",
      "values": "relationships, joy, tradition",
      "languages": ["es-AR", "pt-BR"]
    },
    "Middle East": {
      "style": "Formal, family-values, premium",
      "values": "family, tradition, luxury",
      "languages": ["ar-AE", "he-IL", "en"]
    }
  }

  def __init__(self, api_key: Optional[str] = None):
    """
    Initialize the creative copywriter.

    Args:
      api_key: OpenAI API key (if not provided, reads from env)
    """
    self.api_key = api_key or os.getenv('OPENAI_API_KEY')

    if not self.api_key:
      raise ValueError("OpenAI API key required for copywriting")

    self.client = OpenAI(api_key=self.api_key)
    self.model = "gpt-4o-mini"  # Fast and cost-effective

  def analyze_audience_persona(self, target_audience: str) -> Dict:
    """
    Extract key persona attributes for message tailoring.

    Args:
      target_audience: Description of target audience

    Returns:
      Dictionary with persona insights
    """
    prompt = f"""
    Analyze this target audience for marketing messaging:
    Audience: {target_audience}

    Provide a concise JSON response with:
    {{
      "demographics": "age range and lifestyle",
      "values": ["list", "of", "core", "values"],
      "pain_points": ["main", "challenges"],
      "emotional_triggers": ["positive", "emotions", "to", "evoke"],
      "avoid_terms": ["terms", "to", "avoid"]
    }}
    """

    try:
      response = self.client.chat.completions.create(
        model=self.model,
        messages=[
          {"role": "system", "content": "You are a marketing strategist. Provide JSON responses only."},
          {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Lower for consistent analysis
        max_tokens=200
      )

      # Parse JSON response
      content = response.choices[0].message.content
      # Clean up markdown if present and parse JSON
      return parse_json_response(content)

    except Exception as e:
      print(f"Warning: Persona analysis failed: {e}")
      # Return defaults
      return {
        "demographics": target_audience,
        "values": ["quality", "value"],
        "pain_points": [],
        "emotional_triggers": ["satisfaction", "confidence"],
        "avoid_terms": []
      }

  def generate_optimized_message(self,
                                base_message: str,
                                target_audience: str,
                                target_region: str,
                                products: List[Product],
                                max_length: int = 10) -> Dict:
    """
    Generate optimized marketing messages.

    Args:
      base_message: Original campaign message
      target_audience: Target audience description
      target_region: Target region/market
      products: List of products in campaign
      max_length: Maximum words in message

    Returns:
      Dictionary with optimized messages and metadata
    """
    # Analyze audience persona
    persona = self.analyze_audience_persona(target_audience)

    # Get regional context
    regional_context = self.REGION_CONTEXT.get(
      target_region,
      self.REGION_CONTEXT["North America"]  # Default
    )

    # Build comprehensive prompt
    prompt = f"""
    Create 3 optimized marketing messages for a social media campaign.

    CONTEXT:
    - Original message: "{base_message}"
    - Products: {', '.join([f"{p.name} ({p.description})" for p in products])}
    - Target audience: {target_audience}
    - Region: {target_region}
    - Cultural style: {regional_context['style']}
    - Audience values: {', '.join(persona.get('values', []))}

    REQUIREMENTS:
    - Maximum {max_length} words per message
    - Match the cultural communication style for {target_region}
    - Appeal to the emotional triggers: {', '.join(persona.get('emotional_triggers', []))}
    - Avoid: {', '.join(persona.get('avoid_terms', []))}
    - Focus on benefits, not features
    - Be authentic and engaging

    Provide exactly 3 messages in this JSON format:
    {{
      "messages": [
        {{
          "text": "message here",
          "reasoning": "why this works for the audience",
          "emotional_hook": "the emotion targeted",
          "confidence": 0.95
        }}
      ]
    }}

    Order by effectiveness (best first).
    """

    try:
      response = self.client.chat.completions.create(
        model=self.model,
        messages=[
          {"role": "system", "content": "You are an expert marketing copywriter specializing in culturally-adapted messaging. Provide JSON responses only."},
          {"role": "user", "content": prompt}
        ],
        temperature=0.8,  # Higher for creativity
        max_tokens=400
      )

      # Parse response
      content = response.choices[0].message.content
      result = parse_json_response(content)

      # Add metadata
      return {
        "original": base_message,
        "primary_message": result["messages"][0]["text"],
        "variants": result["messages"],
        "persona_insights": persona,
        "regional_context": regional_context,
        "optimization_applied": True
      }

    except Exception as e:
      print(f"Warning: Message optimization failed: {e}")
      # Fallback to original
      return {
        "original": base_message,
        "primary_message": base_message,
        "variants": [{"text": base_message, "reasoning": "Original message", "confidence": 0.5}],
        "persona_insights": persona,
        "regional_context": regional_context,
        "optimization_applied": False
      }

  def generate_ab_test_variants(self,
                               base_message: str,
                               audience: str,
                               region: str,
                               count: int = 4) -> List[Dict]:
    """
    Generate A/B test variants with different approaches.

    Args:
      base_message: Original message
      audience: Target audience
      region: Target region
      count: Number of variants to generate

    Returns:
      List of variant dictionaries
    """
    approaches = [
      "urgency-driven (limited time, act now)",
      "benefit-focused (what they gain)",
      "emotional (feelings and experiences)",
      "social proof (everyone's choosing)",
      "aspirational (become your best)",
      "problem-solving (fix their pain)"
    ]

    prompt = f"""
    Create {count} A/B test variants of this message, each using a different approach:

    Original: "{base_message}"
    Audience: {audience}
    Region: {region}

    Use these approaches: {', '.join(approaches[:count])}

    Provide JSON with {count} variants:
    {{
      "variants": [
        {{
          "text": "message",
          "approach": "approach used",
          "hypothesis": "why this might work better"
        }}
      ]
    }}

    Keep each under 10 words.
    """

    try:
      response = self.client.chat.completions.create(
        model=self.model,
        messages=[
          {"role": "system", "content": "You are an A/B testing expert. Provide JSON responses only."},
          {"role": "user", "content": prompt}
        ],
        temperature=0.9,  # High for variety
        max_tokens=400
      )

      content = response.choices[0].message.content
      result = parse_json_response(content)
      return result.get("variants", [])

    except Exception as e:
      print(f"Warning: A/B variant generation failed: {e}")
      return []

  def suggest_localizations(self, message: str, region: str) -> Dict:
    """
    Suggest localized versions of the message.

    Args:
      message: Message to localize
      region: Target region

    Returns:
      Dictionary with localized suggestions
    """
    regional_context = self.REGION_CONTEXT.get(
      region,
      self.REGION_CONTEXT["North America"]
    )

    # Only suggest for main languages
    languages = regional_context["languages"][:3]

    if not languages or languages[0] == "en-US":
      return {"suggestions": {}, "note": "English primary market"}

    language_names = {
      "es-MX": "Spanish (Mexico)",
      "fr-CA": "French (Canada)",
      "de-DE": "German",
      "fr-FR": "French",
      "es-ES": "Spanish (Spain)",
      "it-IT": "Italian",
      "pt-BR": "Portuguese (Brazil)",
      "zh-CN": "Chinese (Simplified)",
      "ja-JP": "Japanese",
      "ko-KR": "Korean",
      "ar-AE": "Arabic"
    }

    prompt = f"""
    Translate this marketing message to these languages, maintaining marketing effectiveness:

    Message: "{message}"
    Languages: {', '.join([language_names.get(lang, lang) for lang in languages])}

    Provide culturally-adapted translations (not literal):
    {{
      "translations": {{
        "language_code": "translated message"
      }},
      "notes": "any cultural adaptations made"
    }}
    """

    try:
      response = self.client.chat.completions.create(
        model=self.model,
        messages=[
          {"role": "system", "content": "You are a multilingual marketing translator. Provide JSON responses only."},
          {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
      )

      content = response.choices[0].message.content
      result = parse_json_response(content)
      return {
        "suggestions": result.get("translations", {}),
        "notes": result.get("notes", ""),
        "primary_language": languages[0]
      }

    except Exception as e:
      print(f"Warning: Localization failed: {e}")
      return {"suggestions": {}, "note": "Localization unavailable"}

  def generate_campaign_copy(self, brief) -> Dict:
    """
    Generate complete campaign copy with all optimizations.

    Args:
      brief: CampaignBrief object

    Returns:
      Comprehensive copywriting results
    """
    # Generate optimized messages
    optimized = self.generate_optimized_message(
      base_message=brief.campaign_message,
      target_audience=brief.target_audience,
      target_region=brief.target_region,
      products=brief.products
    )

    # Generate A/B test variants
    ab_variants = self.generate_ab_test_variants(
      base_message=brief.campaign_message,
      audience=brief.target_audience,
      region=brief.target_region,
      count=3
    )

    # Suggest localizations
    localizations = self.suggest_localizations(
      message=optimized["primary_message"],
      region=brief.target_region
    )

    return {
      "optimization": optimized,
      "ab_test_variants": ab_variants,
      "localizations": localizations,
      "selected_message": optimized["primary_message"],
      "confidence_score": optimized["variants"][0].get("confidence", 0.8) if optimized["variants"] else 0.5
    }