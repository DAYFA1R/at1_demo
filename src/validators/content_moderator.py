"""
Content moderation for campaign messages and prompts.
"""

from typing import Dict, List, Optional
from pathlib import Path
import json


class ContentModerator:
  """Checks content for inappropriate or prohibited elements."""

  def __init__(self, config_path: Optional[str] = None):
    """
    Initialize the content moderator.

    Args:
      config_path: Optional path to custom moderation rules
    """
    self.rules = self._load_rules(config_path)
    self.prohibited_words = self.rules.get("prohibited_words", [])
    self.regulated_terms = self.rules.get("regulated_terms", {})

  def _load_rules(self, config_path: Optional[str]) -> dict:
    """
    Load moderation rules from config or use defaults.

    Args:
      config_path: Path to config file

    Returns:
      Dictionary of moderation rules
    """
    default_rules = {
      "prohibited_words": [
        # Offensive/inappropriate
        "offensive", "inappropriate", "scam", "fraud",
        # Misleading claims
        "guaranteed", "risk-free", "no-risk", "instant results",
        # Superlatives without proof
        "miracle", "revolutionary"
      ],
      "regulated_terms": {
        "medical": {
          "terms": ["cure", "prevent", "treat", "heal", "therapy"],
          "disclaimer": "These statements have not been evaluated by the FDA"
        },
        "financial": {
          "terms": ["guaranteed returns", "no risk", "safe investment"],
          "disclaimer": "Past performance does not guarantee future results"
        },
        "superlative": {
          "terms": ["best", "fastest", "cheapest", "#1", "top-rated"],
          "disclaimer": "Requires substantiation or comparative data"
        }
      }
    }

    if config_path and Path(config_path).exists():
      with open(config_path) as f:
        custom_rules = json.load(f)
        # Merge with defaults
        default_rules.update(custom_rules)

    return default_rules

  def check_text_content(self, text: str, context: str = "campaign") -> Dict:
    """
    Check text content for policy violations.

    Args:
      text: Text to check
      context: Context of the text (campaign, prompt, etc.)

    Returns:
      Dictionary with moderation results
    """
    violations = []
    warnings = []
    disclaimers_needed = []

    text_lower = text.lower()

    # Check for prohibited words
    for word in self.prohibited_words:
      if word.lower() in text_lower:
        violations.append({
          "type": "prohibited_word",
          "word": word,
          "severity": "high"
        })

    # Check for regulated terms
    for category, config in self.regulated_terms.items():
      for term in config["terms"]:
        if term.lower() in text_lower:
          warnings.append({
            "type": "regulated_term",
            "category": category,
            "term": term,
            "severity": "medium"
          })
          disclaimers_needed.append(config["disclaimer"])

    # Overall risk assessment
    if violations:
      risk_level = "high"
      approved = False
    elif warnings:
      risk_level = "medium"
      approved = True  # Approved with warnings
    else:
      risk_level = "low"
      approved = True

    return {
      "approved": approved,
      "risk_level": risk_level,
      "violations": violations,
      "warnings": warnings,
      "disclaimers_needed": list(set(disclaimers_needed)),
      "text_checked": text,
      "context": context
    }

  def check_campaign_message(self, message: str, region: Optional[str] = None) -> Dict:
    """
    Check campaign message for compliance.

    Args:
      message: Campaign message text
      region: Target region for region-specific rules

    Returns:
      Moderation results
    """
    result = self.check_text_content(message, context="campaign_message")

    # Add region-specific checks
    if region:
      result["region"] = region
      # Could add region-specific rules here

    return result

  def check_prompt_safety(self, prompt: str) -> Dict:
    """
    Pre-check prompts before sending to DALL-E.

    Args:
      prompt: Generation prompt

    Returns:
      Safety check results
    """
    result = self.check_text_content(prompt, context="generation_prompt")

    # Additional prompt-specific checks
    sensitive_keywords = ["explicit", "violent", "political", "controversial"]
    for keyword in sensitive_keywords:
      if keyword in prompt.lower():
        result["warnings"].append({
          "type": "sensitive_content",
          "keyword": keyword,
          "severity": "medium"
        })
        result["risk_level"] = "medium"

    return result

  def get_summary_report(self) -> Dict:
    """
    Get summary of loaded rules.

    Returns:
      Dictionary with rule counts
    """
    return {
      "prohibited_words_count": len(self.prohibited_words),
      "regulated_categories": list(self.regulated_terms.keys()),
      "total_rules": len(self.prohibited_words) + sum(
        len(cat["terms"]) for cat in self.regulated_terms.values()
      )
    }
