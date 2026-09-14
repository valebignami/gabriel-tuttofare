/* Gabriele — comportamenti della pagina.
   Tre cose sole: la barra in alto che si opacizza, l'ingresso dell'hero,
   e i filetti del percorso che si tracciano quando entrano nello schermo. */

(function () {
  'use strict';

  var ridotto = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* --- barra in alto --- */
  var topbar = document.getElementById('topbar');

  function aggiornaTopbar() {
    topbar.classList.toggle('is-stuck', window.scrollY > 24);
  }

  if (topbar) {
    aggiornaTopbar();
    window.addEventListener('scroll', aggiornaTopbar, { passive: true });
  }

  /* --- menu a scomparsa su mobile --- */
  var bottone = document.getElementById('menu-btn');
  var menu = document.getElementById('menu-mobile');

  /* Le etichette stanno nel markup, non qui: la pagina inglese ne mette di sue. */
  function etichetta(nome, ripiego) {
    return (bottone && bottone.getAttribute('data-label-' + nome)) || ripiego;
  }

  function chiudiMenu() {
    if (!bottone || !menu) return;
    menu.classList.remove('is-open');
    bottone.setAttribute('aria-expanded', 'false');
    bottone.setAttribute('aria-label', etichetta('apri', 'Apri il menu'));
  }

  if (bottone && menu) {
    bottone.addEventListener('click', function () {
      var aperto = menu.classList.toggle('is-open');
      bottone.setAttribute('aria-expanded', aperto ? 'true' : 'false');
      bottone.setAttribute('aria-label', aperto ? etichetta('chiudi', 'Chiudi il menu') : etichetta('apri', 'Apri il menu'));
    });

    /* toccata una voce, il menu si toglie di mezzo */
    var voci = menu.querySelectorAll('a');
    for (var v = 0; v < voci.length; v++) voci[v].addEventListener('click', chiudiMenu);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') chiudiMenu();
    });

    /* se si scorre la pagina con il menu aperto, si chiude da solo */
    window.addEventListener('scroll', function () {
      if (menu.classList.contains('is-open')) chiudiMenu();
    }, { passive: true });
  }

  /* --- ingresso dell'hero: un solo momento, orchestrato --- */
  var saliti = document.querySelectorAll('[data-rise]');

  function mostraHero() {
    for (var i = 0; i < saliti.length; i++) saliti[i].classList.add('is-in');
  }

  if (ridotto) {
    mostraHero();
  } else {
    requestAnimationFrame(function () { requestAnimationFrame(mostraHero); });
  }

  /* --- filetti del percorso --- */
  var passi = document.querySelectorAll('.step');

  if (ridotto || !('IntersectionObserver' in window)) {
    for (var j = 0; j < passi.length; j++) passi[j].classList.add('is-in');
  } else {
    var osservatore = new IntersectionObserver(function (voci) {
      voci.forEach(function (voce) {
        if (voce.isIntersecting) {
          voce.target.classList.add('is-in');
          osservatore.unobserve(voce.target);
        }
      });
    }, { threshold: 0.35, rootMargin: '0px 0px -8% 0px' });

    for (var k = 0; k < passi.length; k++) osservatore.observe(passi[k]);
  }
})();
