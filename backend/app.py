import os
from flask import Flask, request, make_response
from dotenv import load_dotenv
from extensions import db

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///emergency_support.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Simple CORS configuration - manual headers only
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    db.init_app(app)

    with app.app_context():
        from models import Resource, AppSetting
        db.create_all()

        # Create default AppSetting if not exists
        setting = AppSetting.query.first()
        if not setting:
            setting = AppSetting(
                openai_model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
            )
            db.session.add(setting)
            db.session.commit()
            print(f"[INIT] Created default AppSetting (OpenAI model={setting.openai_model})")

    # Register APIs
    from api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Handle OPTIONS requests for CORS preflight
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            return response

    # Global error handler for OpenAI quota errors
    @app.errorhandler(Exception)
    def handle_global_errors(e):
        from openai import RateLimitError
        if isinstance(e, RateLimitError):
            print("[ERROR] OpenAI quota exceeded.")
            return {"error": "OpenAI quota exceeded. Please try again later."}, 429
        raise e  # re-raise all other exceptions normally

    @app.get('/')
    def root():
        return {'ok': True, 'service': 'emergency_support_backend', 'version': '0.2.0'}
    
    @app.get('/test')
    def test():
        return {'message': 'Backend is working!', 'cors': 'enabled'}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
