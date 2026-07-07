import os
import csv
import random
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)

# Define directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, 'food_dataset.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'shelf_life_model.joblib')

def generate_synthetic_dataset():
    """Generates a realistic synthetic dataset for food shelf-life prediction."""
    print("Generating synthetic food dataset...")
    
    categories = ['veg', 'non-veg', 'bakery', 'cooked', 'dairy']
    packaging_types = ['airtight', 'boxed', 'open', 'refrigerated']
    
    headers = ['category', 'prep_age_hours', 'temperature', 'packaging', 'shelf_life_hours']
    
    with open(DATASET_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for _ in range(1000):
            category = random.choice(categories)
            packaging = random.choice(packaging_types)
            
            # Age: how many hours ago it was prepared (0 to 12 hours)
            prep_age = round(random.uniform(0.1, 12.0), 1)
            
            # Ambient temperature at listing time (10 to 42 degrees C)
            temperature = round(random.uniform(10.0, 42.0), 1)
            
            # Base shelf life in hours
            if category == 'veg':
                base_life = 24.0
            elif category == 'non-veg':
                base_life = 12.0
            elif category == 'bakery':
                base_life = 36.0
            elif category == 'cooked':
                base_life = 18.0
            else: # dairy
                base_life = 16.0
                
            # Adjustments based on packaging
            if packaging == 'refrigerated':
                base_life *= 2.5
            elif packaging == 'airtight':
                base_life *= 1.2
            elif packaging == 'open':
                base_life *= 0.6
            # boxed is neutral (1.0)
            
            # Adjustments based on ambient temperature
            # Higher temperatures accelerate spoilage (except if refrigerated)
            if packaging != 'refrigerated':
                temp_factor = 1.0 - (temperature - 20.0) * 0.025
                # Cap factor to prevent negative shelf life
                temp_factor = max(0.2, min(1.3, temp_factor))
                base_life *= temp_factor
                
            # Subtract preparation age (if prepared 5 hours ago, remaining shelf life is less)
            remaining_life = base_life - prep_age
            
            # Add some random noise (-1.5 to +1.5 hours) to simulate real-world variance
            remaining_life += random.uniform(-1.5, 1.5)
            
            # Shelf life cannot be negative, set minimum boundary at 1 hour
            remaining_life = round(max(1.0, remaining_life), 1)
            
            writer.writerow([category, prep_age, temperature, packaging, remaining_life])
            
    print(f"Dataset generated and saved to {DATASET_PATH}")

def train_and_save_model():
    """Encodes categorical data, trains a Random Forest model, and serializes it."""
    if not os.path.exists(DATASET_PATH):
        generate_synthetic_dataset()
        
    print("Loading dataset and preparing training pipeline...")
    df = pd.read_csv(DATASET_PATH)
    
    # One-Hot Encoding for categorical features
    df_encoded = pd.get_dummies(df, columns=['category', 'packaging'], drop_first=False)
    
    # Save the columns to ensure our Django predictor uses matching input shapes
    feature_columns = [col for col in df_encoded.columns if col != 'shelf_life_hours']
    
    X = df_encoded[feature_columns]
    y = df_encoded['shelf_life_hours']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(f"Training Random Forest Regressor on features: {feature_columns}")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)
    
    print(f"Evaluation Metrics:")
    print(f" - Mean Absolute Error: {mae:.2f} hours")
    print(f" - R² Score: {r2:.4f}")
    
    # Package the model and its training features/columns metadata together
    payload = {
        'model': model,
        'feature_columns': feature_columns
    }
    
    joblib.dump(payload, MODEL_PATH)
    print(f"Trained model payload saved successfully to {MODEL_PATH}")

if __name__ == '__main__':
    train_and_save_model()
