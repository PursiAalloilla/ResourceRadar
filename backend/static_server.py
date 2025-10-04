"""
Static file server for frontend apps in Heroku deployment
"""
import os
from flask import Flask, send_from_directory, send_file
from app import create_app

def create_static_app():
    app = create_app()
    
    # Serve client-r (main map app)
    @app.route('/')
    @app.route('/map')
    def serve_client_r():
        return send_file('../client_r/build/index.html')
    
    @app.route('/static/<path:filename>')
    def serve_client_r_static(filename):
        return send_from_directory('../client_r/build/static', filename)
    
    # Serve consumer-app
    @app.route('/consumer')
    def serve_consumer_app():
        return send_file('../consumer-app/dist/index.html')
    
    @app.route('/consumer/<path:filename>')
    def serve_consumer_static(filename):
        return send_from_directory('../consumer-app/dist', filename)
    
    # Serve legal-entity-consumer-app
    @app.route('/legal')
    def serve_legal_app():
        return send_file('../legal-entity-consumer-app/dist/index.html')
    
    @app.route('/legal/<path:filename>')
    def serve_legal_static(filename):
        return send_from_directory('../legal-entity-consumer-app/dist', filename)
    
    return app

if __name__ == '__main__':
    app = create_static_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
