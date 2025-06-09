# 📍 Venue Finder App

AI-powered venue recommendations using OpenAI GPT-4o-mini and Google Maps API. Find perfect meeting spots for groups with real-time travel calculations and personalized transport preferences.

## ✨ Features

- **Dynamic Group Size**: Support for 2-4 people with intuitive controls
- **Personalized Transport**: Individual transport preferences (driving, transit, walking, bicycling)
- **Smart Location Analysis**: Automatic halfway point calculation or custom meeting areas
- **Activity & Mood Matching**: Flexible activity types with mood-based venue selection
- **Real-time Travel Data**: Google Maps API integration for accurate travel times
- **Interactive Maps**: Visual venue display with real geocoding
- **Follow-up Questions**: Chat interface for refining recommendations

## 🚀 Streamlit Cloud Deployment

### Prerequisites
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))
- Google Maps API Key ([Get one here](https://developers.google.com/maps/documentation/javascript/get-api-key))

### Deploy to Streamlit Cloud

1. **Fork this repository** to your GitHub account

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Connect your GitHub account** and select this repository

4. **Set the main file path**: `venue-finder/main.py`

5. **Add secrets** in Streamlit Cloud dashboard:
   ```toml
   OPENAI_API_KEY = "sk-your-openai-api-key-here"
   GOOGLE_MAPS_API_KEY = "your-google-maps-api-key-here"
   ```

6. **Deploy!** Your app will be available at: `https://your-app-name.streamlit.app`

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd venue-finder
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file**:
   ```env
   OPENAI_API_KEY=sk-your-openai-api-key-here
   GOOGLE_MAPS_API_KEY=your-google-maps-api-key-here
   ```

4. **Run the app**:
   ```bash
   streamlit run main.py
   ```

5. **Open**: http://localhost:8501

## 🔧 Configuration

### Required API Keys

**OpenAI API Key**:
- Used for AI venue recommendations and follow-up questions
- Get from: https://platform.openai.com/api-keys
- Model used: GPT-4o-mini (cost-effective and fast)

**Google Maps API Key**:
- Used for geocoding, travel time calculations, and direction links
- Required APIs: Geocoding API, Directions API
- Get from: https://console.cloud.google.com/apis/credentials

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o-mini | Yes |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key | Yes |

## 📱 Usage

1. **Set Group Size**: Choose 2-4 people using the ➕/➖ buttons
2. **Enter Locations**: Add starting locations for each person
3. **Choose Transport**: Select transport preferences (or "Any" for flexibility)
4. **Set Meeting Details**: Pick date, time, activity type, and mood
5. **Optional**: Specify preferred meeting area or let AI find the halfway point
6. **Get Recommendations**: Click "Find Perfect Venues" for AI-powered suggestions
7. **Ask Follow-ups**: Refine results with natural language questions

## 🎯 Example Use Cases

- **Date Planning**: "Restaurant" + "First Date" mood for romantic venues
- **Business Meetings**: "Coffee/Cafe" + "Business Meeting" for professional spaces  
- **Group Hangouts**: "Any" activity + "Casual Hangout" for flexible options
- **After Work**: "Bar/Pub" + "Energetic & Fun" for social venues

## 🛠️ Technical Details

- **Framework**: Streamlit
- **AI Model**: OpenAI GPT-4o-mini
- **Maps**: Google Maps API (Geocoding + Directions)
- **Deployment**: Streamlit Cloud ready
- **Dependencies**: Minimal, no external servers required

## 📊 Performance

- **Response Time**: ~3-5 seconds for venue recommendations
- **Travel Calculations**: Real-time with Google Maps API
- **Scalability**: Serverless deployment, handles concurrent users
- **Cost**: ~$0.01-0.05 per recommendation (depending on complexity)

---

Made with ❤️ for finding the perfect meeting spots! 🎯 