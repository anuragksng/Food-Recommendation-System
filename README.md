# Smart Food Recommendation System

A personalized food recommendation platform that leverages machine learning to provide tailored culinary suggestions, adapting to individual user preferences and dietary needs.

## Features

- **User Authentication**: Secure login and signup with user profile management
- **Weather-Based Recommendations**: Food suggestions based on current weather conditions
- **Personalized Preferences**: Customized recommendations based on spice level, sugar level, and meal type preferences
- **Smart Learning**: Continuously improves suggestions based on user feedback (likes/dislikes)
- **Strict Dietary Filtering**: Ensures users only see food items that match their dietary preferences
- **Interactive UI**: Intuitive interface for browsing and interacting with recommendations

## Technical Highlights

### Data Standardization

The system includes data standardization to ensure consistent food type classification:

- Original food data used a 'Veg_Non' column with inconsistent values
- The standardizer creates a new 'Type' column with fixed values: 'Vegetarian' or 'NonVegetarian'
- Both columns are maintained for backward compatibility
- All recommendation and filtering functions now use the standardized Type column with proper fallback

### Dietary Filtering

Multiple layers of filtering ensure users only see food items compatible with their dietary preferences:

1. Initial database query filtering
2. ML-based filtering during recommendation generation
3. Strict type filtering as a final safeguard

### Machine Learning Features

- **Hybrid Recommendation System**: Combines content-based and collaborative filtering
- **TF-IDF Vectorization**: For text processing and feature extraction
- **KNN Algorithm**: For finding similar food items
- **User Similarity Calculation**: For collaborative filtering recommendations

## Getting Started

1. Log in with username "test" and password "test" for demonstration
2. Or create a new account with your preferences
3. Browse recommendations, like/dislike items, and search for specific dishes
4. The system learns from your interactions to provide better suggestions over time

## Data Sources

The recommendation system uses several data sources:

- User preferences data
- Food item database with detailed attributes
- Weather-food associations
- User feedback and ratings history

## Technical Architecture

- Streamlit for the interactive frontend
- PostgreSQL database with SQLAlchemy ORM
- Machine learning models for recommendation generation
- Strict filtering mechanisms for preference matching

## Run At
streamlit run app.py --server.port 8501
http://localhost:8501
http://127.0.0.1:8501

![image](https://github.com/user-attachments/assets/4de769ae-054d-40f1-932f-7a206d81eb44)
![image](https://github.com/user-attachments/assets/20313c37-2477-4bd7-9079-c2a4d8bf5814)
![image](https://github.com/user-attachments/assets/e36d9814-435a-4054-b31a-4be94ef94091)
![image](https://github.com/user-attachments/assets/2916f0b0-f96f-435c-bca7-d138b568f594)






