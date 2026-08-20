// Utilidades globales mínimas
// La lógica de cada página está en su propio template <script>

// Marcar nav activo
document.querySelectorAll('.nb').forEach(el => {
  if (el.getAttribute('href') === window.location.pathname) {
    el.classList.add('act');
  }
});
