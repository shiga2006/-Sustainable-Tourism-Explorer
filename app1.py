import streamlit as st
import pandas as pd
import random
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from openai import OpenAI

# Page configuration
st.set_page_config(page_title="Sustainable Tourism Explorer", layout="wide")

conn = st.connection("snowflake")

# Initialize OpenRouter client with your API key (⚠️ Use secrets in production)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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",
)

# Connect to Snowflake
conn = st.connection("snowflake")

# Load and cache data
@st.cache_data(ttl=600)
def load_data():
    footfall = conn.query("SELECT * FROM SNOWFLAKE_LEARNING_DB.PUBLIC.TOURIST_FOOTFALL")
    eco_zones = conn.query("SELECT * FROM SNOWFLAKE_LEARNING_DB.PUBLIC.ECO_ZONES")
    heritage = conn.query("SELECT * FROM SNOWFLAKE_LEARNING_DB.PUBLIC.HERITAGE_SITES")
    initiatives = conn.query("SELECT * FROM SNOWFLAKE_LEARNING_DB.PUBLIC.GOVERNMENT_INITIATIVES")
    tips = conn.query("SELECT * FROM SNOWFLAKE_LEARNING_DB.PUBLIC.SUSTAINABLE_TOURISM_TIPS")
    ticket = conn.query("SELECT * FROM SNOWFLAKE_LEARNING_DB.PUBLIC.TICKET_PRICE")
    quiz_df = conn.query("SELECT * FROM SNOWFLAKE_LEARNING_DB.PUBLIC.ECO_QUIZZ")
    return footfall, eco_zones, heritage, initiatives, tips, ticket, quiz_df

# Load data
footfall, eco_zones, heritage, initiatives, tips, ticket, quiz_df = load_data()

# Title and Description
st.title("🏞️ Sustainable Tourism Explorer")
st.markdown("""
Welcome to the Sustainable Tourism Dashboard! Here, you can:
- Explore tourism footfall trends 📈  
- Discover ecotourism zones 🌿  
- Learn about heritage sites 🏛️  
- Stay updated with government initiatives 🏢  
- Read sustainable tourism tips 🌍  
- Test your knowledge with our Eco Quiz 🎯  
- Chat with our Sustainable Tourism Bot 🤖  
- View Interactive Tourist Map 🗺️
""")

# Sidebar Navigation
page = st.sidebar.selectbox("📌 Choose a section", [
    "Tourism Footfall", "Eco-tourism Zones", "Heritage Sites",
    "Government Initiatives", "Sustainable Tourism Tips",
    "Ticket Price", "Eco Quiz 🎯", "Chat with Tourist Bot 🤖",
    "Tourist Map 🗺️"
])

# Sections
if page == "Tourism Footfall":
    st.header("📊 Tourist Footfall")
    footfall["Year"] = pd.to_numeric(footfall["YEAR"], errors="coerce")
    footfall["Domestic_Visitors"] = pd.to_numeric(footfall["DOMESTIC_VISITORS"], errors="coerce")
    footfall["Foreign_Visitors"] = pd.to_numeric(footfall["FOREIGN_VISITORS"], errors="coerce")
    yearly = footfall.groupby("Year")[["Domestic_Visitors", "Foreign_Visitors"]].sum()
    st.line_chart(yearly)
    statewise = footfall.groupby("STATE")[["Domestic_Visitors", "Foreign_Visitors"]].sum()
    st.bar_chart(statewise)
    st.dataframe(footfall)

elif page == "Eco-tourism Zones":
    st.header("🌿 Eco-tourism Zones")
    if {"Latitude", "Longitude"}.issubset(eco_zones.columns):
        st.map(eco_zones.rename(columns={"Latitude": "lat", "Longitude": "lon"}))
    st.dataframe(eco_zones)

elif page == "Heritage Sites":
    st.header("🏛 Heritage Sites")
    if {"Latitude", "Longitude"}.issubset(heritage.columns):
        st.map(heritage.rename(columns={"Latitude": "lat", "Longitude": "lon"}))
    st.dataframe(heritage)

elif page == "Government Initiatives":
    st.header("🏢 Government Initiatives")
    for _, row in initiatives.iterrows():
        with st.expander(f"{row['SCHEME_NAME']} ({row['YEAR']})"):
            st.write(f"Category: {row.get('CATEGORY', 'N/A')}")
            st.write(f"State: {row.get('STATE', 'All')}")
            st.write(f"Budget: ₹{row.get('BUDGET_CR','N/A')} Cr")
            st.write(f"Description: {row.get('DESCRIPTION', 'No description')}")

elif page == "Sustainable Tourism Tips":
    st.header("💡 Sustainable Tourism Tips")
    for _, row in tips.iterrows():
        with st.expander(f"Tip {row['C1']} - {row['C2']}"):
            st.write(row["C3"])

elif page == "Ticket Price":
    st.header("🎟 Ticket Price Info")
    ticket.columns = ticket.columns.str.strip()
    if "PLACE" in ticket.columns and "AVG_TICKET_PRICE_INR" in ticket.columns:
        ticket["AVG_TICKET_PRICE_INR"] = pd.to_numeric(ticket["AVG_TICKET_PRICE_INR"], errors="coerce")
        ticket_sorted = ticket.dropna(subset=["PLACE"]).sort_values("AVG_TICKET_PRICE_INR", ascending=False)
        st.bar_chart(ticket_sorted.set_index("PLACE")["AVG_TICKET_PRICE_INR"])
    st.dataframe(ticket[["PLACE", "STATE", "AVG_TICKET_PRICE_INR", "SEASONAL_PEAK"]])

elif page == "Eco Quiz 🎯":
    st.header("🎯 Eco Quiz")
    if "quiz_data" not in st.session_state:
        quiz_df = quiz_df.dropna(subset=["QUESTION", "OPTION1", "OPTION2", "OPTION3", "CORRECT_ANSWER"])
        quiz_data = quiz_df.sample(n=5, random_state=random.randint(1, 9999)).reset_index(drop=True)
        st.session_state.quiz_data = quiz_data
        st.session_state.user_answers = [None] * 5
        st.session_state.score = 0
        st.session_state.submitted = False

    quiz_data = st.session_state.quiz_data
    for i, row in quiz_data.iterrows():
        st.subheader(f"Q{i+1}: {row['QUESTION']}")
        options = [row["OPTION1"], row["OPTION2"], row["OPTION3"]]
        st.session_state.user_answers[i] = st.radio(f"Your answer for Q{i+1}:", options, key=f"q_{i}")

    if st.button("Submit Quiz"):
        score = 0
        for i, row in quiz_data.iterrows():
            if st.session_state.user_answers[i] == row["CORRECT_ANSWER"]:
                score += 1
        st.session_state.score = score
        st.session_state.submitted = True
        st.rerun()

    if st.session_state.get("submitted", False):
        st.success(f"✅ You scored {st.session_state.score} out of 5!")
        if st.session_state.score >= 3:
            st.balloons()
        else:
            st.info("🌱 Keep learning and try again!")

        if st.button("Play Again"):
            for key in list(st.session_state.keys()):
                if key.startswith("q_") or key in ["quiz_data", "user_answers", "score", "submitted"]:
                    del st.session_state[key]
            st.rerun()

elif page == "Chat with Tourist Bot 🤖":
    st.header("🤖 Chat with Sustainable Tourism Bot")
    st.markdown("Ask me anything about sustainable tourism, eco-travel tips, or local culture!")

    # System prompt
    sustainable_prompt = """
You are a tourism and sustainability expert on the Sustainable Tourism Explorer platform.

Answer questions accurately, clearly, and concisely about:
- Eco-friendly travel practices
- Local culture and traditions
- Responsible tourism
- Environmental impact
- Conservation efforts
- Green accommodations
- Biodiversity
- Community engagement
- Sustainable transportation options
- Cultural heritage preservation
- Local cuisine and sustainable food practices
- Wildlife conservation
- Ethical wildlife tourism  
- Sustainable tourism certifications
- Tips for reducing carbon footprint while traveling
- Best practices for minimizing waste while traveling
- How to support local economies through tourism
- How to engage with local communities respectfully
- How to choose eco-friendly tour operators
- How to participate in local conservation projects
- How to travel mindfully and respectfully

Ensure responses promote sustainability, preserve heritage, and encourage travelers to make environmentally and culturally responsible choices.
"""

    # Session state for chat
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": sustainable_prompt}]

    # Show previous messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        elif msg["role"] == "assistant":
            st.markdown(f"**Tourist Bot:** {msg['content']}")

    # Input and reply
    user_input = st.text_input("✍ Ask your question here:", key="chat_input")
    if st.button("Send"):
        if not user_input.strip():
            st.warning("Please enter a question.")
        else:
            st.session_state.messages.append({"role": "user", "content": user_input})
            try:
                response = client.chat.completions.create(
                    model="cognitivecomputations/dolphin3.0-r1-mistral-24b:free",
                    messages=st.session_state.messages,
                    max_tokens=500,
                    temperature=0.7,
                )
                reply = response.choices[0].message.content.strip()
                st.session_state.messages.append({"role": "assistant", "content": reply})
                st.rerun()
            except Exception as e:
                st.error(f"API error: {e}")

elif page == "Tourist Map 🗺️":
    st.header("🗺️ Interactive Map of Tourist Places")

    # Fetch data from Snowflake LAT_LONG table
    lat_long = conn.query("SELECT * FROM SNOWFLAKE_LEARNING_DB.PUBLIC.LAT_LONG")

    # Sanitize column names
    lat_long.columns = lat_long.columns.str.strip().str.lower().str.replace(" ", "_")

    # Ensure numeric conversions
    lat_long["annual_footfall_in_thousands"] = pd.to_numeric(lat_long["annual_footfall_in_thousands"], errors="coerce")
    lat_long["latitude"] = pd.to_numeric(lat_long["latitude"], errors="coerce")
    lat_long["longitude"] = pd.to_numeric(lat_long["longitude"], errors="coerce")

    # Drop rows with missing coordinates
    lat_long.dropna(subset=["latitude", "longitude"], inplace=True)

    # Create Folium map
    m = folium.Map(location=[22.5937, 78.9629], zoom_start=5)
    marker_cluster = MarkerCluster().add_to(m)

    # Color scale function
    def get_color(footfall):
        if pd.isna(footfall):
            return "gray"
        elif footfall > 5000:
            return "blue"
        elif footfall > 1000:
            return "orange"
        else:
            return "green"

    # Add points to the map
    for _, row in lat_long.iterrows():
        place = row.get("place", "Unknown")
        state = row.get("state", "")
        footfall = row["annual_footfall_in_thousands"]
        lat = row["latitude"]
        lon = row["longitude"]
        color = get_color(footfall)

        popup_text = f"<b>{place}</b><br>{state}<br>Footfall: {footfall}K"

        folium.CircleMarker(
            location=[lat, lon],
            radius=max((footfall or 0) / 100, 3),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(marker_cluster)

    # Display the map in Streamlit
    st_folium(m, width=700, height=500)
