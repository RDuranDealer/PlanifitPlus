import os
from flask import Flask, render_template, redirect, url_for
from models import db
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)

    # Base de datos
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///rpg_tenis.db')
    # Railway entrega postgres:// pero SQLAlchemy necesita postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI']        = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-cambiar-en-produccion')

    db.init_app(app)

    # Registrar blueprints
    from routes.rutinas  import bp as rutinas_bp
    from routes.progreso import bp as progreso_bp
    from routes.config   import bp as config_bp

    app.register_blueprint(rutinas_bp)
    app.register_blueprint(progreso_bp)
    app.register_blueprint(config_bp)

    # Rutas HTML
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/dia/<int:dia_id>')
    def dia(dia_id):
        return render_template('dia.html', dia_id=dia_id)

    @app.route('/historial')
    def historial():
        return render_template('historial.html')

    @app.route('/configuracion')
    def configuracion():
        return render_template('configuracion.html')

    # Crear tablas y seed al iniciar si no existen
    with app.app_context():
        db.create_all()
        _seed_inicial()

    return app


def _seed_inicial():
    """Carga datos iniciales solo si la tabla está vacía."""
    from models import Ejercicio
    if Ejercicio.query.count() == 0:
        try:
            from seed import seed
            seed()
        except Exception as e:
            print(f"Error en seed: {e}")


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
