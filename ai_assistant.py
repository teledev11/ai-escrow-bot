"""
Contextual AI Assistant for Transaction Guidance
Provides intelligent assistance throughout the escrow process
"""

import os
import json
import logging
from datetime import datetime
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

class TransactionAIAssistant:
    """AI Assistant for providing contextual transaction guidance"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # Do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        
    async def analyze_transaction_risk(self, transaction_data):
        """Analyze transaction risk and provide recommendations"""
        try:
            prompt = f"""
            As an expert escrow transaction advisor, analyze this transaction for potential risks and provide guidance:
            
            Transaction Details:
            - Service: {transaction_data.get('service', 'Unknown')}
            - Amount: {transaction_data.get('amount', '0')} {transaction_data.get('currency', 'BTC')}
            - Seller: {transaction_data.get('seller', 'Unknown')}
            - Seller Rating: {transaction_data.get('seller_rating', 'Unknown')}
            - Transaction Type: {transaction_data.get('type', 'service')}
            - Delivery Method: {transaction_data.get('delivery_method', 'digital')}
            
            Provide a comprehensive risk analysis in JSON format with:
            1. Overall risk level (low/medium/high)
            2. Specific risk factors identified
            3. Recommended precautions
            4. Trust score assessment
            5. Suggested next steps
            
            Respond only with valid JSON in this format:
            {{
                "risk_level": "low/medium/high",
                "risk_score": 1-100,
                "risk_factors": ["factor1", "factor2"],
                "recommendations": ["rec1", "rec2"],
                "trust_assessment": "assessment text",
                "next_steps": ["step1", "step2"],
                "safety_tips": ["tip1", "tip2"]
            }}
            """
            
            response = await self._make_openai_request(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Risk analysis error: {e}")
            return self._fallback_risk_analysis()
    
    async def provide_seller_guidance(self, seller_data, transaction_context):
        """Provide guidance for evaluating sellers"""
        try:
            prompt = f"""
            As an escrow transaction expert, evaluate this seller and provide buyer guidance:
            
            Seller Information:
            - Username: {seller_data.get('username', 'Unknown')}
            - Rating: {seller_data.get('rating', 'Unknown')}
            - Total Trades: {seller_data.get('total_trades', 0)}
            - Success Rate: {seller_data.get('success_rate', 0)}%
            - Specialization: {seller_data.get('specialization', 'General')}
            - Response Time: {seller_data.get('response_time', 'Unknown')}
            - Member Since: {seller_data.get('member_since', 'Unknown')}
            
            Transaction Context:
            - Service Requested: {transaction_context.get('service', 'Unknown')}
            - Amount: {transaction_context.get('amount', '0')}
            - Urgency: {transaction_context.get('urgency', 'normal')}
            
            Provide seller evaluation in JSON format with:
            1. Seller trustworthiness assessment
            2. Compatibility with requested service
            3. Recommended negotiation points
            4. Red flags (if any)
            5. Confidence level in this seller
            
            Respond only with valid JSON.
            """
            
            response = await self._make_openai_request(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Seller guidance error: {e}")
            return self._fallback_seller_guidance()
    
    async def generate_transaction_steps(self, transaction_type, user_role):
        """Generate step-by-step transaction guidance"""
        try:
            prompt = f"""
            Create a detailed step-by-step guide for a {user_role} in a {transaction_type} escrow transaction.
            
            Context:
            - User Role: {user_role} (buyer/seller)
            - Transaction Type: {transaction_type}
            - Platform: Telegram Escrow Bot
            
            Provide clear, actionable steps in JSON format with:
            1. Pre-transaction preparation
            2. During transaction execution
            3. Post-transaction completion
            4. Safety checkpoints
            5. What to do if issues arise
            
            Make it beginner-friendly but comprehensive. Include timing estimates and safety tips.
            
            Respond only with valid JSON in this format:
            {{
                "pre_transaction": [
                    {{"step": 1, "action": "action description", "time_estimate": "5 minutes", "safety_tip": "tip"}}
                ],
                "during_transaction": [...],
                "post_transaction": [...],
                "safety_checkpoints": [...],
                "troubleshooting": [...]
            }}
            """
            
            response = await self._make_openai_request(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Transaction steps error: {e}")
            return self._fallback_transaction_steps(user_role)
    
    async def provide_contextual_advice(self, user_query, context):
        """Provide contextual advice based on user query and situation"""
        try:
            prompt = f"""
            As an expert escrow advisor, provide helpful advice for this user query in their current context:
            
            User Query: "{user_query}"
            
            Current Context:
            - User Status: {context.get('user_status', 'new')}
            - Current Action: {context.get('current_action', 'browsing')}
            - Transaction Stage: {context.get('transaction_stage', 'none')}
            - Previous Transactions: {context.get('transaction_count', 0)}
            - Platform Experience: {context.get('experience_level', 'beginner')}
            
            Provide helpful, specific advice that:
            1. Directly addresses their query
            2. Considers their experience level
            3. Includes relevant safety tips
            4. Suggests next actions
            5. Prevents common mistakes
            
            Keep the response conversational, helpful, and under 200 words.
            Focus on actionable advice specific to their situation.
            """
            
            response = await self._make_openai_request(prompt)
            return response.strip()
            
        except Exception as e:
            logger.error(f"Contextual advice error: {e}")
            return "I'm here to help with your escrow questions! Feel free to ask about transactions, safety, or any concerns you have."
    
    async def analyze_conversation_sentiment(self, messages):
        """Analyze conversation sentiment between buyer and seller"""
        try:
            prompt = f"""
            Analyze the sentiment and communication quality in this buyer-seller conversation:
            
            Messages: {json.dumps(messages[:10])}  # Last 10 messages
            
            Provide analysis in JSON format:
            {{
                "overall_sentiment": "positive/neutral/negative",
                "communication_quality": "excellent/good/poor",
                "trust_indicators": ["indicator1", "indicator2"],
                "warning_signs": ["warning1", "warning2"],
                "recommendations": ["rec1", "rec2"]
            }}
            """
            
            response = await self._make_openai_request(prompt)
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"overall_sentiment": "neutral", "communication_quality": "unknown"}
    
    async def _make_openai_request(self, prompt):
        """Make request to OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert escrow transaction advisor with deep knowledge of crypto transactions, digital services, and online marketplace safety. Provide accurate, helpful, and safety-focused advice."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"} if "JSON" in prompt else None,
                max_tokens=1000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _fallback_risk_analysis(self):
        """Fallback risk analysis when AI is unavailable"""
        return {
            "risk_level": "medium",
            "risk_score": 50,
            "risk_factors": ["Limited seller information", "Standard transaction risks"],
            "recommendations": ["Verify seller credentials", "Use escrow protection", "Communicate clearly"],
            "trust_assessment": "Proceed with standard precautions",
            "next_steps": ["Review seller profile", "Confirm service details", "Initiate escrow payment"],
            "safety_tips": ["Never pay outside escrow", "Keep all communications documented"]
        }
    
    def _fallback_seller_guidance(self):
        """Fallback seller guidance when AI is unavailable"""
        return {
            "trustworthiness": "Standard verification recommended",
            "compatibility": "Review seller's service portfolio",
            "negotiation_points": ["Delivery timeline", "Service specifications", "Payment terms"],
            "red_flags": "None identified - proceed with standard caution",
            "confidence_level": "Medium - verify credentials before proceeding"
        }
    
    def _fallback_transaction_steps(self, user_role):
        """Fallback transaction steps when AI is unavailable"""
        if user_role == "buyer":
            return {
                "pre_transaction": [
                    {"step": 1, "action": "Review seller profile and ratings", "time_estimate": "5 minutes", "safety_tip": "Check feedback from previous buyers"}
                ],
                "during_transaction": [
                    {"step": 1, "action": "Send payment to escrow", "time_estimate": "10 minutes", "safety_tip": "Never pay directly to seller"}
                ],
                "post_transaction": [
                    {"step": 1, "action": "Confirm receipt of goods/service", "time_estimate": "2 minutes", "safety_tip": "Only confirm if completely satisfied"}
                ]
            }
        else:
            return {
                "pre_transaction": [
                    {"step": 1, "action": "Prepare service/goods for delivery", "time_estimate": "Variable", "safety_tip": "Ensure quality meets description"}
                ],
                "during_transaction": [
                    {"step": 1, "action": "Deliver as promised", "time_estimate": "Variable", "safety_tip": "Maintain professional communication"}
                ],
                "post_transaction": [
                    {"step": 1, "action": "Wait for buyer confirmation", "time_estimate": "24-48 hours", "safety_tip": "Follow up politely if needed"}
                ]
            }

# Global AI assistant instance
ai_assistant = TransactionAIAssistant()