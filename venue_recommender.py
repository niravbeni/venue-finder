"""
Venue recommendation system using OpenAI GPT-4o-mini and Google Maps API
Optimized for Streamlit Cloud deployment
"""

import os
import asyncio
import requests
import urllib.parse
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VenueRecommender:
    """Main class for handling venue recommendations"""
    
    def __init__(self):
        pass
        
    async def initialize(self):
        """Initialize method kept for backward compatibility"""
        pass
    
    def get_recommendations(
        self,
        locations: List[str],
        activity: str,
        meeting_area: Optional[str] = None,
        mood: Optional[str] = None,
        notes: Optional[str] = None,
        meeting_datetime: Optional[datetime] = None,
        transport_preferences: Optional[List[str]] = None
    ) -> str:
        """
        Get venue recommendations based on starting locations and preferences
        
        Args:
            locations: List of starting locations for group members
            activity: Type of activity/venue needed
            meeting_area: Optional preferred area for meeting (if None, finds halfway point)
            mood: Mood/objective of the meetup (e.g., "First Date", "Business Meeting")
            notes: Additional requirements or preferences
            meeting_datetime: Date and time of meeting for traffic calculations
            transport_preferences: List of transportation preferences per person (same order as locations)
        
        Returns:
            Formatted recommendations as string
        """
        # Set default transport preferences if not provided
        if transport_preferences is None:
            transport_preferences = ["driving"] * len(locations)
        
        # Ensure transport preferences match locations length
        while len(transport_preferences) < len(locations):
            transport_preferences.append("driving")
        
        # Set default meeting time if not provided
        if meeting_datetime is None:
            meeting_datetime = datetime.now()
        
        # Use asyncio to run the async function
        return asyncio.run(self._get_detailed_venue_recommendations_with_real_times(
            locations=locations,
            activity_type=activity,
            transport_preferences=transport_preferences,
            meeting_datetime=meeting_datetime,
            meeting_area=meeting_area,
            mood=mood,
            notes=notes
        ))
    
    async def _get_detailed_venue_recommendations_with_real_times(
        self,
        locations: List[str],
        activity_type: str,
        transport_preferences: List[str],
        meeting_datetime: datetime,
        meeting_area: Optional[str] = None,
        mood: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        Get venue recommendations with exact travel times from Google Maps API
        """
        
        # Check if API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return "❌ OPENAI_API_KEY not found in environment variables."
        
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=openai_api_key)
            
            # Generate venue suggestions first with enhanced prompt
            locations_text = "\n".join([f"{i+1}. {loc}" for i, loc in enumerate(locations)])
            
            venue_prompt = f"""Based on these starting locations:
{locations_text}

Meeting requirements:
- Activity: {activity_type.lower() if activity_type != "Any" else "flexible (any type of venue)"}
- Mood/Objective: {mood.lower() if mood and mood != "Any" else "flexible/open to suggestions"}
- Meeting area: {"in " + meeting_area if meeting_area else " roughly halfway between these locations"}
{"- Additional notes: " + notes if notes and notes.strip() else ""}

Please suggest EXACTLY 5 specific, high-quality venues that would be excellent for this group{
    f" AND match the {mood.lower()} vibe" if mood and mood != "Any" else " with versatile atmosphere"
}. 

Consider:
- Venue quality and reputation
{f"- Suitability for {activity_type.lower()}" if activity_type != "Any" else "- Versatility for different types of activities"}
{f"- Perfect match for {mood.lower()} atmosphere" if mood and mood != "Any" else "- Flexible atmosphere that works for various moods"}
- Good accessibility for the group
- {"Meeting the specific requirements: " + notes if notes and notes.strip() else ""}

CRITICAL: You MUST provide exactly 5 venues. Provide ONLY real venue names with proper, complete addresses including street name, area, and postcode. Do NOT list ranges of numbers or incomplete addresses.

Provide in this EXACT format (no additional text, just these 5 lines):
1. [Real Venue Name] - [Number] [Street Name], [Area], [City] [Postcode]
2. [Real Venue Name] - [Number] [Street Name], [Area], [City] [Postcode]
3. [Real Venue Name] - [Number] [Street Name], [Area], [City] [Postcode]
4. [Real Venue Name] - [Number] [Street Name], [Area], [City] [Postcode]
5. [Real Venue Name] - [Number] [Street Name], [Area], [City] [Postcode]

Examples of correct format:
- The Ivy Chelsea Garden - 197 King's Road, Chelsea, London SW3 5ED
- Dishoom Covent Garden - 12 Upper St Martin's Lane, Covent Garden, London WC2H 9FB
- The Shard Restaurant - 31 St Thomas Street, London Bridge, London SE1 9QU

IMPORTANT: Return ONLY the 5 numbered venue lines, nothing else. No introduction, no explanation, just the 5 venues{
    f" that specifically match the {mood.lower()} mood/objective" if mood and mood != "Any" else " that are versatile and work for different preferences"
}."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a local venue expert. Provide exactly 5 specific, real venue recommendations with exact addresses. Be concise and follow the format exactly."},
                    {"role": "user", "content": venue_prompt}
                ],
                max_tokens=600,
                temperature=0.1
            )
            
            venue_suggestions = response.choices[0].message.content or "No venues found"
            
            # Parse venue suggestions to extract addresses
            venue_lines = [line.strip() for line in venue_suggestions.split('\n') if line.strip() and any(char.isdigit() for char in line)]
            
            # Filter out malformed addresses
            filtered_venue_lines = []
            for line in venue_lines:
                # Skip lines with too many numbers (likely malformed addresses)
                comma_count = line.count(',')
                number_sequences = len([part for part in line.split() if any(char.isdigit() for char in part)])
                
                # Accept only reasonable addresses (not lists of numbers)
                if comma_count <= 10 and number_sequences <= 8 and len(line) <= 200:
                    filtered_venue_lines.append(line)
            
            # If no valid venues after filtering, use original lines but with warning
            if not filtered_venue_lines:
                filtered_venue_lines = venue_lines[:5]
                
            # If still no venues, create some fallback recommendations based on location
            if len(filtered_venue_lines) < 3:
                fallback_venues = [
                    "The Hoxton Holborn - 199-206 High Holborn, Holborn, London WC1V 7BD",
                    "Dishoom King's Cross - 5 Stable Street, King's Cross, London N1C 4AB", 
                    "The Ivy City Garden - 1 Angel Court, Bank, London EC2R 7HJ",
                    "Sketch - 9 Conduit Street, Mayfair, London W1S 2XG",
                    "Duck & Waffle - 110 Bishopsgate, Liverpool Street, London EC2N 4AY"
                ]
                
                # Add fallbacks up to 5 total venues
                for fallback in fallback_venues:
                    if len(filtered_venue_lines) >= 5:
                        break
                    if fallback not in filtered_venue_lines:
                        filtered_venue_lines.append(fallback)
            
            detailed_results = []
            
            for venue_line in filtered_venue_lines[:5]:  # Process up to 5 venues
                # Extract venue name and address
                if " - " in venue_line:
                    venue_part = venue_line.split(" - ", 1)[1]
                    venue_name = venue_line.split(" - ")[0].split(". ", 1)[-1]
                else:
                    venue_part = venue_line.split(". ", 1)[1] if ". " in venue_line else venue_line
                    venue_name = venue_part.split(",")[0]
                
                venue_address = venue_part
                
                # Get venue description from AI
                desc_prompt = f"""In 1-2 sentences, describe why {venue_name} is a good choice{
                    f" for {activity_type.lower()}" if activity_type != "Any" else " as a versatile venue"
                }{
                    f" with a {mood.lower()} vibe" if mood and mood != "Any" else " that works for various moods"
                }. Consider atmosphere, {
                    "food quality, " if activity_type in ["Restaurant", "Coffee/Cafe"] or activity_type == "Any" else ""
                }location, ambiance, and{
                    f" how it matches the {mood.lower()} mood" if mood and mood != "Any" else " its versatility for different preferences"
                }."""
                
                try:
                    desc_response = await client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a venue expert. Provide brief, helpful descriptions."},
                            {"role": "user", "content": desc_prompt}
                        ],
                        max_tokens=100,
                        temperature=0.3
                    )
                    venue_description = desc_response.choices[0].message.content or "Great venue for your meetup."
                except:
                    venue_description = f"Excellent {activity_type.lower()} venue in a convenient location."
                
                # Calculate exact travel times for each person
                travel_details = []
                total_duration_seconds = 0
                max_duration_seconds = 0
                
                for i, (location, transport) in enumerate(zip(locations, transport_preferences)):
                    # Handle "Any" transport mode by using the most efficient option (driving)
                    actual_transport = transport if transport != "Any" else "driving"
                    
                    travel_info = await self._get_travel_time_and_route(
                        origin=location,
                        destination=venue_address,
                        mode=actual_transport,
                        departure_time=meeting_datetime
                    )
                    
                    person_number = i + 1  # 1, 2, 3, 4
                    transport_emoji = {"Any": "🔄", "driving": "🚗", "transit": "🚌", "walking": "🚶", "bicycling": "🚴"}
                    emoji = transport_emoji.get(transport, "🚗")
                    
                    # Format travel detail for each person on separate lines
                    transport_display = f"{transport.title()}" if transport != "Any" else f"Any (using {actual_transport.title()})"
                    travel_detail = f"• **Person {person_number}** ({emoji} {transport_display}): Leave at {travel_info['departure_time']} • Journey time: {travel_info['duration']} • <a href='{travel_info['google_maps_link']}' target='_blank'>Get directions</a>"
                    
                    travel_details.append(travel_detail)
                    
                    # Add to total time and track max time (for fairness ranking)
                    if 'raw_duration_seconds' in travel_info:
                        duration = travel_info['raw_duration_seconds']
                        total_duration_seconds += duration
                        max_duration_seconds = max(max_duration_seconds, duration)
                
                # Calculate average travel time
                avg_time_minutes = total_duration_seconds // len(locations) // 60 if total_duration_seconds > 0 else 0
                max_time_minutes = max_duration_seconds // 60 if max_duration_seconds > 0 else 0
                
                # Calculate suitability score (lower is better)
                suitability_score = (max_duration_seconds * 1.5) + total_duration_seconds
                
                # Format venue recommendation with all information
                venue_recommendation = f"""
## 📍 {venue_name}

**Address**: {venue_address}

**Why this venue**: {venue_description}

**🚶‍♂️ Travel Details:**  
{('<br>'.join(travel_details))}

**📊 Summary**: Average {avg_time_minutes} mins • Longest journey {max_time_minutes} mins

---

"""
                detailed_results.append((suitability_score, venue_recommendation))
            
            # Sort venues by suitability score (best first)
            detailed_results.sort(key=lambda x: x[0])
            
            # Format final response
            final_response = f"""# 🎯 Venue Recommendations

**Meeting Details:**
• **📅 When**: {meeting_datetime.strftime('%A, %B %d, %Y at %I:%M %p')}
• **🎪 Activity**: {activity_type if activity_type != "Any" else "Any (flexible)"}
• **🎭 Mood/Objective**: {mood if mood and mood != "Any" else "Any (open to suggestions)"}
• **👥 Group**: {len(locations)} people
{"• **📍 Area**: " + meeting_area if meeting_area else "• **🎯 Strategy**: Halfway between all locations"}
{"• **📝 Notes**: " + notes if notes and notes.strip() else ""}

{('\n\n'.join([result[1] for result in detailed_results]))}

💡 **Tips**: Venues ranked by convenience and fairness. All times calculated to arrive by {meeting_datetime.strftime('%I:%M %p')}. {
    f"Venues selected to match your {mood.lower()} vibe!" if mood and mood != "Any" 
    else "Versatile venues selected to accommodate different preferences!"
}
"""
            
            return final_response
            
        except Exception as e:
            return f"❌ Error getting detailed recommendations: {str(e)}"

    async def _get_travel_time_and_route(
        self,
        origin: str, 
        destination: str, 
        mode: str,
        departure_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get exact travel time and detailed route information using Google Maps API
        """
        google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        
        if not google_maps_api_key:
            return {
                "duration": "API key not available",
                "distance": "Unknown",
                "route_info": "Google Maps API key required for real-time data",
                "detailed_steps": [],
                "departure_time": "Unknown",
                "arrival_time": "Unknown",
                "google_maps_link": self._generate_google_maps_link(origin, destination, mode)
            }
        
        try:
            # Google Maps Directions API
            base_url = "https://maps.googleapis.com/maps/api/directions/json"
            
            # Map our transport modes to Google's
            google_mode_map = {
                "driving": "driving",
                "transit": "transit", 
                "walking": "walking",
                "bicycling": "bicycling"
            }
            
            params = {
                "origin": origin,
                "destination": destination,
                "mode": google_mode_map.get(mode, "driving"),
                "key": google_maps_api_key,
                "units": "metric"
            }
            
            # Add departure time for transit and driving (for traffic)
            if departure_time and mode in ["transit", "driving"]:
                # Convert to Unix timestamp
                timestamp = int(departure_time.timestamp())
                params["departure_time"] = str(timestamp)
            
            # Add alternatives for better route options
            if mode == "transit":
                params["alternatives"] = "true"
            
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK" and data["routes"]:
                route = data["routes"][0]  # Take the first route
                leg = route["legs"][0]     # Take the first leg
                
                # Extract duration and distance
                duration_text = leg["duration"]["text"]
                distance_text = leg["distance"]["text"]
                duration_seconds = leg["duration"]["value"]
                
                # Calculate departure and arrival times
                if departure_time:
                    # Meeting time is the arrival time
                    arrival_time = departure_time
                    # Calculate when they need to leave (meeting time minus travel duration)
                    departure_time_calc = datetime.fromtimestamp(departure_time.timestamp() - duration_seconds)
                else:
                    # Default case
                    arrival_time = datetime.now()
                    departure_time_calc = datetime.fromtimestamp(arrival_time.timestamp() - duration_seconds)
                
                # Generate Google Maps link with specific transportation mode
                google_maps_link = self._generate_google_maps_link(origin, destination, mode)
                
                return {
                    "duration": duration_text,
                    "distance": distance_text,
                    "route_info": f"{duration_text} via {mode}",
                    "detailed_steps": [],
                    "departure_time": departure_time_calc.strftime("%I:%M %p"),
                    "arrival_time": arrival_time.strftime("%I:%M %p") if arrival_time else "Unknown",
                    "google_maps_link": google_maps_link,
                    "raw_duration_seconds": duration_seconds
                }
            else:
                error_msg = data.get("error_message", "Route not found")
                return {
                    "duration": "Route not available",
                    "distance": "Unknown", 
                    "route_info": f"Error: {error_msg}",
                    "detailed_steps": [],
                    "departure_time": "Unknown",
                    "arrival_time": "Unknown",
                    "google_maps_link": self._generate_google_maps_link(origin, destination, mode)
                }
                
        except Exception as e:
            return {
                "duration": "Error calculating time",
                "distance": "Unknown",
                "route_info": f"API Error: {str(e)}",
                "detailed_steps": [],
                "departure_time": "Unknown", 
                "arrival_time": "Unknown",
                "google_maps_link": self._generate_google_maps_link(origin, destination, mode)
            }

    def _generate_google_maps_link(self, origin: str, destination: str, mode: str) -> str:
        """Generate a Google Maps link with specific transportation mode"""
        
        # Map our modes to Google Maps URL parameters
        mode_map = {
            "driving": "driving",
            "transit": "transit",
            "walking": "walking", 
            "bicycling": "bicycling"
        }
        
        google_mode = mode_map.get(mode, "driving")
        
        # Encode the addresses for URL
        origin_encoded = urllib.parse.quote_plus(origin)
        destination_encoded = urllib.parse.quote_plus(destination)
        
        # Build Google Maps URL with working format
        return f"https://www.google.com/maps/dir/{origin_encoded}/{destination_encoded}/@?hl=en&travelmode={google_mode}"
    
    def handle_followup_query(self, query: str, context: str = "") -> str:
        """
        Handle follow-up questions using async processing
        """
        return asyncio.run(self._handle_followup_async(query, context))
    
    async def _handle_followup_async(self, query: str, context: str = "") -> str:
        """
        Internal async method for handling follow-up questions
        """
        # Check if API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            return "❌ OPENAI_API_KEY not found. Please check your .env file configuration."
        
        try:
            # Use direct OpenAI API for follow-up questions
            import openai
            client = openai.AsyncOpenAI(api_key=openai_api_key)
            
            # Improved prompt that emphasizes using the context
            system_prompt = """You are a venue finder assistant helping with follow-up questions about previously recommended venues. 

IMPORTANT: You have been provided with specific venue recommendations in the context. When answering questions, you should:
1. Reference the SPECIFIC venues that were previously recommended by name
2. Use the details from those recommendations (addresses, descriptions, travel times)
3. Answer based on the actual venues provided, not generic categories
4. If asked about suitability for different purposes (like dates), evaluate each specific venue mentioned

Always refer to the actual venue names and details from the context, not generic venue types."""
            
            # Create a more structured prompt
            if context.strip():
                full_prompt = f"""Based on these previously recommended venues:

{context}

Please answer this follow-up question by referring to the SPECIFIC venues listed above:

Question: {query}

Remember to:
- Mention specific venue names from the recommendations
- Use the actual details provided about each venue
- Give personalized advice based on the venues that were suggested
- If discussing suitability for different activities (like dates), evaluate each specific venue"""
            else:
                full_prompt = f"""I don't have the context of previous venue recommendations. 

Question: {query}

I need the original venue recommendations to give you a specific answer about which venues would be good for your request. Could you please ask for new venue recommendations first?"""
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content or "No response received from API"
                
        except Exception as e:
            return f"Error processing question: {str(e)}" 