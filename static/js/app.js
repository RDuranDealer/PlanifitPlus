async function logout() {
  await fetch('/api/usuarios/logout', {method: 'POST'});
  window.location.href = '/';
}
