"""
Streamlit Venue Finder App
AI-powered venue recommendations using OpenAI GPT-4o-mini and Google Maps API
Optimized for Streamlit Cloud deployment
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import re
import requests
from datetime import datetime, time
from venue_recommender import VenueRecommender
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="Venue Finder",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'recommender' not in st.session_state:
        try:
            st.session_state.recommender = VenueRecommender()
        except Exception as e:
            st.error(f"Error initializing venue recommender: {str(e)}")
            st.error("Please ensure your API keys are set correctly in the .env file")
            st.stop()
    
    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = ""
    
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    
    # Initialize number of users (default to 2)
    if 'num_users' not in st.session_state:
        st.session_state.num_users = 2
    
    # Initialize venue locations for map
    if 'venue_locations' not in st.session_state:
        st.session_state.venue_locations = []

def extract_venue_locations(recommendations_text):
    """Extract venue names and addresses from recommendations text"""
    venues = []
    
    # Look for venue sections that start with "## 📍"
    venue_pattern = r'## 📍 (.+?)\n\s*\*\*Address\*\*:\s*(.+?)\n'
    matches = re.findall(venue_pattern, recommendations_text, re.DOTALL)
    
    for name, address in matches:
        venues.append({
            'name': name.strip(),
            'address': address.strip()
        })
    
    return venues

def create_venue_map(venues=None):
    """Create a map with venue pins"""
    # Default center (London)
    m = folium.Map(location=[51.5074, -0.1278], zoom_start=12)
    
    if venues:
        # Add venue pins
        for i, venue in enumerate(venues):
            # Try to get real coordinates if Google Maps API is available
            load_dotenv()
            google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
            
            if google_maps_api_key:
                # Try to geocode the real address
                try:
                    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
                    params = {
                        "address": venue['address'],
                        "key": google_maps_api_key
                    }
                    
                    response = requests.get(base_url, params=params, timeout=5)
                    data = response.json()
                    
                    if data["status"] == "OK" and data["results"]:
                        location = data["results"][0]["geometry"]["location"]
                        lat = location["lat"]
                        lng = location["lng"]
                    else:
                        # Fallback to approximate coordinates
                        lat = 51.5074 + (i * 0.01) - 0.02
                        lng = -0.1278 + (i * 0.01) - 0.02
                except:
                    # Fallback to approximate coordinates
                    lat = 51.5074 + (i * 0.01) - 0.02
                    lng = -0.1278 + (i * 0.01) - 0.02
            else:
                # Use approximate London coordinates with slight offsets
                lat = 51.5074 + (i * 0.01) - 0.02
                lng = -0.1278 + (i * 0.01) - 0.02
            
            folium.Marker(
                [lat, lng],
                popup=f"<b>{venue['name']}</b><br>{venue['address']}",
                tooltip=venue['name'],
                icon=folium.Icon(color='red', icon='cutlery')
            ).add_to(m)
    else:
        # Add a default marker for demonstration
        folium.Marker(
            [51.5074, -0.1278],
            popup="London Center",
            tooltip="Click for more info",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    return m

def main():
    """Main application function"""
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("📍 Venue Finder")
    st.markdown("*Find perfect meeting spots using AI and Google Maps data*")
    
    # Check for environment file
    if not os.path.exists('.env'):
        st.warning("⚠️ Please create a `.env` file with your API keys. See `env_template.txt` for reference.")
    else:
        # Check if API keys are properly configured
        load_dotenv()
        
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key or len(openai_key) < 20 or '\n' in openai_key:
            st.error("🔧 **API Key Configuration Issue**")
            st.markdown("""
            Your OPENAI_API_KEY appears to be missing or incorrectly formatted. Please:
            
            1. Edit your `.env` file
            2. Ensure the OPENAI_API_KEY is on a **single line** without line breaks
            3. The key should start with `sk-` and be quite long (50+ characters)
            4. Save the file and restart the app
            
            **Example format:**
            ```
            OPENAI_API_KEY=sk-your-very-long-api-key-here
            GOOGLE_MAPS_API_KEY=your-google-maps-key-here
            ```
            """)
            st.stop()
    
    # User management controls (outside form to avoid form resets)
    st.header("👥 Group Size")
    
    # Better layout for the group size controls
    col_info, col_controls = st.columns([2, 1])
    
    with col_info:
        st.write(f"**{st.session_state.num_users} people** will be meeting")
        if st.session_state.num_users == 2:
            st.caption("💡 Perfect for dates, coffee chats, or 1-on-1 meetings")
        elif st.session_state.num_users == 3:
            st.caption("💡 Great for small group meetups")
        else:  # 4 people
            st.caption("💡 Maximum group size - Perfect for team meetings or double dates")
    
    with col_controls:
        col_add, col_remove = st.columns(2)
        with col_add:
            st.button(
                "➕ Add",
                disabled=(st.session_state.num_users >= 4),
                on_click=lambda: setattr(st.session_state, 'num_users', min(4, st.session_state.num_users + 1)),
                use_container_width=True,
                type="secondary"
            )
        with col_remove:
            st.button(
                "➖ Remove", 
                disabled=(st.session_state.num_users <= 2),
                on_click=lambda: setattr(st.session_state, 'num_users', max(2, st.session_state.num_users - 1)),
                use_container_width=True,
                type="secondary"
            )
    
    st.divider()
    
    # Create two main columns: form and map
    col_form, col_map = st.columns([3, 2])
    
    with col_form:
        st.header("📝 Meeting Details")
        
        # Input form
        with st.form("venue_form"):
            # Starting locations section
            st.subheader(f"📍 Starting Locations ({st.session_state.num_users} people)")
            
            # Create columns for locations and transport preferences
            locations = []
            transport_preferences = []
            
            for i in range(st.session_state.num_users):
                col_loc, col_transport = st.columns([2, 1])
                
                with col_loc:
                    location = st.text_input(
                        f"Person {i+1} Location",
                        key=f"location_{i}",
                        placeholder=f"e.g., London Bridge Station, SE1 9SP",
                        help="Enter a specific address, landmark, or station for best results"
                    )
                    locations.append(location)
                
                with col_transport:
                    transport = st.selectbox(
                        f"Person {i+1} Transport",
                        ["Any", "driving", "transit", "walking", "bicycling"],
                        key=f"transport_{i}",
                        format_func=lambda x: {
                            "Any": "🔄 Any",
                            "driving": "🚗 Driving",
                            "transit": "🚌 Transit", 
                            "walking": "🚶 Walking",
                            "bicycling": "🚴 Bicycling"
                        }[x],
                        help="Choose preferred transport or 'Any' if flexible"
                    )
                    transport_preferences.append(transport)
            
            st.divider()
            
            # Meeting area preference with better layout
            st.subheader("🎯 Meeting Area Preference")
            col_check, col_area = st.columns([1, 2])
            
            with col_check:
                specify_area = st.checkbox("Specify preferred area", help="Uncheck to find venues at the geographic center")
            
            with col_area:
                meeting_area = st.text_input(
                    "Preferred meeting area",
                    disabled=not specify_area,
                    placeholder="e.g., Central London, Shoreditch, Camden",
                    help="Enter a neighborhood, district, or general area"
                )
            
            st.divider()
            
            # Meeting time section
            st.subheader("⏰ Meeting Time")
            col_date, col_time = st.columns(2)
            
            with col_date:
                meeting_date = st.date_input("Meeting date", value=datetime.now().date())
            
            with col_time:
                meeting_time = st.time_input("Meeting time", value=datetime.now().time())
            
            meeting_datetime = datetime.combine(meeting_date, meeting_time)
            
            st.divider()
            
            # Activity and notes section
            st.subheader("🎪 Activity & Requirements")
            col_activity, col_mood = st.columns([1, 1])
            
            with col_activity:
                activity = st.selectbox(
                    "Activity type",
                    ["Any", "Restaurant", "Coffee/Cafe", "Bar/Pub", "Park", "Museum", "Shopping", "Cinema", "Gym/Fitness", "Other"],
                    help="Choose the type of venue you're looking for, or 'Any' if flexible"
                )
            
            with col_mood:
                mood = st.selectbox(
                    "Mood/Objective",
                    ["Any", "First Date", "Conversation Spot", "Live Music", "Good for After Activities", "Vibey/Trendy", "Quiet & Intimate", "Energetic & Fun", "Business Meeting", "Celebration", "Casual Hangout", "Other"],
                    help="Choose the vibe or purpose of your meetup, or 'Any' if no specific preference"
                )
            
            # Notes section (full width)
            notes = st.text_area(
                "Additional notes",
                placeholder="e.g., vegetarian options, outdoor seating, wheelchair accessible...",
                height=100,
                help="Any special requirements or preferences"
            )
            
            # Submit button with better styling
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "🔍 Find Perfect Venues",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Validate inputs - only check the locations for the current number of users
                valid_locations = [loc for loc in locations[:st.session_state.num_users] if loc.strip()]
                valid_transport_prefs = transport_preferences[:st.session_state.num_users]
                
                if len(valid_locations) < st.session_state.num_users:
                    missing_count = st.session_state.num_users - len(valid_locations)
                    st.error(f"Please enter all {st.session_state.num_users} starting locations. {missing_count} location(s) missing.")
                elif specify_area and not meeting_area.strip():
                    st.error("Please enter a preferred meeting area or uncheck the option to find venues at the geographic center.")
                elif not activity.strip():
                    st.error("Please select or specify an activity.")
                else:
                    # Get recommendations
                    with st.spinner("🤖 AI is finding the perfect venues for you..."):
                        try:
                            recommendations = st.session_state.recommender.get_recommendations(
                                locations=valid_locations,
                                meeting_area=meeting_area if specify_area else None,
                                activity=activity,
                                mood=mood,
                                notes=notes,
                                meeting_datetime=meeting_datetime,
                                transport_preferences=valid_transport_prefs
                            )
                            
                            st.session_state.recommendations = recommendations
                            
                            # Extract venue locations for the map
                            venues = extract_venue_locations(recommendations)
                            st.session_state.venue_locations = venues
                            
                            st.session_state.conversation_history.append({
                                'type': 'query',
                                'locations': valid_locations,
                                'meeting_area': meeting_area if specify_area else "Geographic center",
                                'activity': activity,
                                'mood': mood,
                                'notes': notes,
                                'meeting_datetime': meeting_datetime,
                                'transport_preferences': valid_transport_prefs,
                                'response': recommendations
                            })
                            
                        except Exception as e:
                            st.error(f"Error getting recommendations: {str(e)}")

    with col_map:
        st.header("📍 Venue Map")
        
        # Display map with venues if available
        try:
            if st.session_state.venue_locations:
                st.caption(f"🎯 Showing {len(st.session_state.venue_locations)} recommended venues")
                map_obj = create_venue_map(st.session_state.venue_locations)
            else:
                st.caption("Map will show venue pins after recommendations")
                map_obj = create_venue_map()
            
            map_data = st_folium(map_obj, height=400, width=None)
        except Exception as e:
            st.error(f"Error displaying map: {str(e)}")
            st.info("Map visualization temporarily unavailable")
    
    # Results section (full width)
    if st.session_state.recommendations:
        # Display recommendations without duplicate header
        st.markdown(st.session_state.recommendations, unsafe_allow_html=True)
        
        # Follow-up questions section
        st.header("💬 Ask Follow-up Questions")
        st.caption("Ask for refinements like 'show me options within 30 minutes of location A' or 'find vegetarian-friendly alternatives'")
        
        with st.form("followup_form"):
            followup_query = st.text_input(
                "Your question:",
                placeholder="e.g., What about venues with shorter walking times?"
            )
            
            followup_submitted = st.form_submit_button("Ask", type="secondary")
            
            if followup_submitted and followup_query.strip():
                with st.spinner("🤖 Getting additional information..."):
                    try:
                        # Create context from conversation history with more details
                        context = ""
                        if st.session_state.conversation_history:
                            last_interaction = st.session_state.conversation_history[-1]
                            if last_interaction['type'] == 'query':
                                # Include the full recommendation response for better context
                                context = f"""PREVIOUS VENUE RECOMMENDATIONS:

Meeting Details:
- Locations: {', '.join(last_interaction['locations'])}
- Activity: {last_interaction['activity']}
- Mood: {last_interaction['mood']}
- Meeting Area: {last_interaction['meeting_area']}
- Date/Time: {last_interaction['meeting_datetime'].strftime('%A, %B %d, %Y at %I:%M %p')}

{last_interaction['response']}"""
                            elif last_interaction['type'] == 'followup':
                                # If last interaction was a follow-up, get the original recommendations
                                for interaction in reversed(st.session_state.conversation_history):
                                    if interaction['type'] == 'query':
                                        context = f"""PREVIOUS VENUE RECOMMENDATIONS:

Meeting Details:
- Locations: {', '.join(interaction['locations'])}
- Activity: {interaction['activity']}
- Mood: {interaction['mood']}
- Meeting Area: {interaction['meeting_area']}
- Date/Time: {interaction['meeting_datetime'].strftime('%A, %B %d, %Y at %I:%M %p')}

{interaction['response']}"""
                                        break
                        
                        followup_response = st.session_state.recommender.handle_followup_query(
                            query=followup_query,
                            context=context
                        )
                        
                        st.subheader("Follow-up Response:")
                        st.markdown(followup_response, unsafe_allow_html=True)
                        
                        # Add to conversation history
                        st.session_state.conversation_history.append({
                            'type': 'followup',
                            'query': followup_query,
                            'response': followup_response
                        })
                        
                    except Exception as e:
                        st.error(f"Error processing follow-up: {str(e)}")

if __name__ == "__main__":
    main() 