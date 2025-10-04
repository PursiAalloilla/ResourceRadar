import os
from flask import Flask
from dotenv import load_dotenv
from extensions import db
from flask_cors import CORS

load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///emergency_support.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    with app.app_context():
        from models import Resource, AppSetting
        db.create_all()

        # Create default AppSetting if not exists
        setting = AppSetting.query.first()
        if not setting:
            setting = AppSetting(
                llm_backend=os.getenv('LLM_BACKEND', 'hf'),
                hf_model_id=os.getenv('HF_MODEL_ID', 'microsoft/Phi-3.5-MoE-instruct'),
                hf_device=os.getenv('HF_DEVICE', 'cpu'),
                openai_model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            )
            db.session.add(setting)
            db.session.commit()
            print(f"[INIT] Created default AppSetting (backend={setting.llm_backend})")

        # --- Preload HF model to avoid cold-start ---
        if setting.llm_backend == 'hf' or True:  # always preload so fallback is instant
            print("[INIT] Preloading Hugging Face model...")
            from services.llm import preload_hf_model
            preload_hf_model(setting.hf_model_id, setting.hf_device)
            print("[INIT] Hugging Face model loaded.")

    # Register APIs
    from api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Global error handler for OpenAI quota errors
    @app.errorhandler(Exception)
    def handle_global_errors(e):
        from openai import RateLimitError
        if isinstance(e, RateLimitError):
            from models import AppSetting
            print("[ERROR] OpenAI quota exceeded. Falling back to Hugging Face.")
            s = AppSetting.query.first()
            if s:
                s.llm_backend = 'hf'
                db.session.commit()
            return {"error": "OpenAI quota exceeded. Backend switched to Hugging Face."}, 429
        raise e  # re-raise all other exceptions normally

    @app.get('/')
    def root():
        return {'ok': True, 'service': 'emergency_support_backend', 'version': '0.2.0'}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
