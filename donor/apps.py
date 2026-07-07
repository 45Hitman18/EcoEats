import os
import joblib
from django.apps import AppConfig


class DonorConfig(AppConfig):
    name = 'donor'
    model = None
    feature_columns = None
    
    def ready(self):
        import donor.signals  # Import signals to register them
        
        # Load machine learning model on startup
        import sys
        if 'manage.py' not in sys.argv or 'runserver' in sys.argv:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.abspath(os.path.join(base_dir, '../ml_assets/shelf_life_model.joblib'))
            if os.path.exists(model_path):
                try:
                    payload = joblib.load(model_path)
                    DonorConfig.model = payload.get('model')
                    DonorConfig.feature_columns = payload.get('feature_columns')
                    print("✅ ML Food Shelf-Life model loaded successfully on startup!")
                except Exception as e:
                    print(f"❌ Failed to load ML Food Shelf-Life model: {str(e)}")
            else:
                print("⚠️ ML Food Shelf-Life model binary not found. Please run train_model.py first.")
