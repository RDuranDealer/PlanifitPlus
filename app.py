import os
from flask import Flask, render_template, session, redirect, url_for
from models import db
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)

    database_url = os.environ.get('DATABASE_URL', 'sqlite:///rpg_tenis.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI']        = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

    db.init_app(app)

    # Blueprints
    from routes.usuarios import bp as usuarios_bp
    from routes.rutinas  import bp as rutinas_bp
    from routes.progreso import bp as progreso_bp
    from routes.config   import bp as config_bp
    from routes.admin      import bp as admin_bp
    from routes.assessment import bp as assessment_bp

    for bp in [usuarios_bp, rutinas_bp, progreso_bp, config_bp, admin_bp, assessment_bp]:
        app.register_blueprint(bp)

    # ── Rutas HTML ────────────────────────────────────────────────────────────

    @app.route('/')
    def index():
        """Selector de usuario (pantalla inicial)."""
        return render_template('index.html')

    @app.route('/app')
    def app_main():
        """App principal — requiere usuario en sesión."""
        if not session.get('usuario_id'):
            return redirect(url_for('index'))
        return render_template('app.html')

    @app.route('/historial')
    def historial():
        if not session.get('usuario_id'):
            return redirect(url_for('index'))
        return render_template('historial.html')

    @app.route('/assessment-usuario/<int:uid>')
    def assessment_usuario_view(uid):
        from routes.assessment import assessment_usuario
        return assessment_usuario(uid)

    @app.route('/configuracion')
    def configuracion():
        if not session.get('usuario_id'):
            return redirect(url_for('index'))
        return render_template('configuracion.html')

    # Crear tablas y seed inicial
    with app.app_context():
        db.create_all()
        _seed_inicial()

    return app


def _seed_inicial():
    from models import Usuario
    if Usuario.query.count() == 0:
        try:
            from seed import seed
            seed()
        except Exception as e:
            print(f"Error en seed: {e}")


app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
