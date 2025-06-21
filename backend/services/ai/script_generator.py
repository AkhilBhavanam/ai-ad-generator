import openai
import os
import logging
from typing import List, Dict, Any
import asyncio
import json
from backend.core.models import ProductData, AdScript

logger = logging.getLogger(__name__)

class AdScriptGenerator:
    """Generates ad scripts using OpenAI based on product data"""
    
    def __init__(self):
        # Initialize OpenAI client with better error handling
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.client = None
        
        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
                logger.warning("Will use fallback script generation")
                self.client = None
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables")
        
        # Ad script templates for different tones
        self.templates = {
            "exciting": {
                "system_prompt": "You are a HIGH-ENERGY advertising copywriter who creates ELECTRIFYING, POWERFUL ad scripts that GRAB ATTENTION and drive MASSIVE conversions. Use exciting language, power words, and create URGENCY that makes people want to BUY NOW!",
                "tone_keywords": ["AMAZING", "INCREDIBLE", "BREAKTHROUGH", "REVOLUTIONARY", "MUST-HAVE", "TRANSFORM", "GAME-CHANGING", "EXPLOSIVE", "MIND-BLOWING", "ULTIMATE"]
            },
            "professional": {
                "system_prompt": "You are a professional advertising copywriter who creates sophisticated, trustworthy ad scripts that highlight quality and reliability.",
                "tone_keywords": ["quality", "reliable", "trusted", "premium", "professional", "proven"]
            },
            "casual": {
                "system_prompt": "You are a friendly advertising copywriter who creates casual, relatable ad scripts that feel like recommendations from a friend.",
                "tone_keywords": ["love", "enjoy", "perfect", "awesome", "great", "recommend"]
            }
        }
    
    async def generate_ad_script(self, product_data: ProductData, tone: str = "exciting") -> AdScript:
        """Generate ad script from product data"""
        try:
            if not self.client:
                logger.warning("OpenAI client not available, using fallback script generation")
                return self._generate_fallback_script(product_data, tone)
            
            # Prepare the prompt
            prompt = self._create_prompt(product_data, tone)
            
            # Generate script using OpenAI
            response = await self._call_openai(prompt, tone)
            
            # Parse the response into AdScript
            ad_script = self._parse_response(response, tone)
            
            logger.info(f"Generated ad script for product: {product_data.title}")
            return ad_script
            
        except Exception as e:
            logger.error(f"Error generating ad script: {str(e)}")
            return self._generate_fallback_script(product_data, tone)
    
    def _create_prompt(self, product_data: ProductData, tone: str) -> str:
        """Create OpenAI prompt from product data"""
        
        features_text = "\n".join(f"- {feature}" for feature in product_data.key_features[:5])
        
        prompt = f"""
Create a compelling 15-second video ad script for the following product:

PRODUCT INFORMATION:
Title: {product_data.title}
Description: {product_data.description or 'No description available'}
Price: {product_data.price or 'Price not specified'}
Brand: {product_data.brand or 'Unknown brand'}
Key Features:
{features_text}
Rating: {product_data.rating or 'No rating'}

REQUIREMENTS:
- Create a {tone} and engaging 15-second video ad script
- Target audience: General consumers
- Include a strong hook to grab attention in first 3 seconds
- Identify a problem the product solves
- Present the product as the solution
- Highlight 2-3 key benefits
- End with a compelling call-to-action
- Keep language {tone} and persuasive

RESPONSE FORMAT (JSON):
{{
    "hook": "Opening line that grabs attention",
    "problem": "Problem the product solves",
    "solution": "How this product solves the problem",
    "benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
    "call_to_action": "Compelling CTA",
    "duration_seconds": 15,
    "tone": "{tone}",
    "target_audience": "general"
}}

Generate a script that would work perfectly for a 15-second video ad:
"""
        return prompt
    
    async def _call_openai(self, prompt: str, tone: str) -> str:
        """Make async call to OpenAI API"""
        try:
            template = self.templates.get(tone, self.templates["exciting"])
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": template["system_prompt"]},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def _parse_response(self, response: str, tone: str) -> AdScript:
        """Parse OpenAI response into AdScript object"""
        try:
            # Try to parse JSON response
            if response.strip().startswith('{'):
                data = json.loads(response)
                return AdScript(
                    hook=data.get("hook", "Discover something amazing!"),
                    problem=data.get("problem", "Looking for the perfect solution?"),
                    solution=data.get("solution", "This product is exactly what you need!"),
                    benefits=data.get("benefits", ["High quality", "Great value", "Perfect fit"]),
                    call_to_action=data.get("call_to_action", "Get yours today!"),
                    duration_seconds=data.get("duration_seconds", 15),
                    tone=data.get("tone", tone),
                    target_audience=data.get("target_audience", "general")
                )
            else:
                # Parse text response manually
                return self._parse_text_response(response, tone)
                
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON response, attempting text parsing")
            return self._parse_text_response(response, tone)
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            return self._generate_simple_fallback(tone)
    
    def _parse_text_response(self, response: str, tone: str) -> AdScript:
        """Parse text response when JSON parsing fails"""
        lines = response.split('\n')
        
        hook = "Discover something amazing!"
        problem = "Looking for the perfect solution?"
        solution = "This product is exactly what you need!"
        benefits = ["High quality", "Great value", "Perfect fit"]
        cta = "Get yours today!"
        
        # Simple parsing logic
        for line in lines:
            line = line.strip()
            if line.lower().startswith('hook:'):
                hook = line[5:].strip()
            elif line.lower().startswith('problem:'):
                problem = line[8:].strip()
            elif line.lower().startswith('solution:'):
                solution = line[9:].strip()
            elif line.lower().startswith('call'):
                cta = line.split(':', 1)[1].strip() if ':' in line else line
        
        return AdScript(
            hook=hook,
            problem=problem,
            solution=solution,
            benefits=benefits,
            call_to_action=cta,
            tone=tone
        )
    
    def _generate_fallback_script(self, product_data: ProductData, tone: str) -> AdScript:
        """Generate fallback script when OpenAI is not available"""
        logger.info("Generating fallback ad script")
        
        title = product_data.title or "Amazing Product"
        price = product_data.price or "great price"
        
        templates = {
            "exciting": {
                "hook": f"🔥 INCREDIBLE! The {title} is HERE!",
                "problem": "Sick of products that DON'T DELIVER?",
                "solution": f"The {title} is the GAME-CHANGING solution you've been waiting for!",
                "benefits": ["REVOLUTIONARY design that TRANSFORMS everything", "UNBEATABLE quality you can TRUST", "MIND-BLOWING value that saves you MONEY"],
                "cta": "DON'T WAIT! Order now and change your life FOREVER!"
            },
            "professional": {
                "hook": f"Discover the premium {title}",
                "problem": "Looking for professional-grade quality?",
                "solution": f"The {title} delivers superior performance",
                "benefits": ["Professional quality", "Reliable performance", "Trusted by experts"],
                "cta": "Invest in quality today"
            },
            "casual": {
                "hook": f"You're going to love the {title}!",
                "problem": "Need something that just works?",
                "solution": f"The {title} is perfect for you",
                "benefits": ["Super easy to use", "Really affordable", "You'll love it"],
                "cta": "Grab yours now!"
            }
        }
        
        template = templates.get(tone, templates["exciting"])
        
        # Customize based on product data
        if product_data.key_features:
            template["benefits"] = product_data.key_features[:3]
        
        return AdScript(
            hook=template["hook"],
            problem=template["problem"],
            solution=template["solution"],
            benefits=template["benefits"],
            call_to_action=template["cta"],
            tone=tone
        )
    
    def _generate_simple_fallback(self, tone: str) -> AdScript:
        """Generate very simple fallback when all else fails"""
        return AdScript(
            hook="Discover something amazing!",
            problem="Looking for the perfect solution?",
            solution="This product is exactly what you need!",
            benefits=["High quality", "Great value", "Perfect for you"],
            call_to_action="Get yours today!",
            tone=tone
        ) 