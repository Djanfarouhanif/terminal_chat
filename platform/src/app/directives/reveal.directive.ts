import {
  Directive,
  ElementRef,
  afterNextRender,
  inject,
  input,
} from '@angular/core';

/**
 * Fait apparaître l'élément en douceur (fondu + glissement) quand il entre
 * dans le viewport au scroll. Réutilisable sur n'importe quelle balise :
 *
 *   <div appReveal>…</div>
 *   <div appReveal [revealDelay]="120">…</div>   <!-- décalage en ms (effet cascade) -->
 *   <div appReveal revealFrom="left">…</div>      <!-- up | down | left | right -->
 */
@Directive({
  selector: '[appReveal]',
  host: {
    '[attr.data-reveal]': 'revealFrom()',
    '[style.transition-delay.ms]': 'revealDelay()',
  },
})
export class RevealDirective {
  /** Décalage avant l'apparition, en ms (pour un effet cascade). */
  revealDelay = input(0);
  /** Direction d'où l'élément glisse : up (défaut), down, left, right. */
  revealFrom = input<'up' | 'down' | 'left' | 'right'>('up');
  /** Fraction visible qui déclenche l'apparition (0 → 1). */
  revealThreshold = input(0.15);

  private host = inject<ElementRef<HTMLElement>>(ElementRef);

  constructor() {
    // Navigateur uniquement (pas au pré-rendu SSR).
    afterNextRender(() => {
      const el = this.host.nativeElement;

      // Accessibilité : pas d'animation → visible tout de suite.
      const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (reduce || typeof IntersectionObserver === 'undefined') {
        el.classList.add('is-visible');
        return;
      }

      const observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (entry.isIntersecting) {
              el.classList.add('is-visible');
              observer.unobserve(el); // une seule fois
            }
          }
        },
        { threshold: this.revealThreshold(), rootMargin: '0px 0px -8% 0px' },
      );
      observer.observe(el);
    });
  }
}
