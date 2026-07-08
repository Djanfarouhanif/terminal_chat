import {
  Component,
  DestroyRef,
  afterNextRender,
  inject,
} from '@angular/core';
import { RouterOutlet, RouterLink, Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs';
import Lenis from 'lenis';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  private router = inject(Router);
  private destroyRef = inject(DestroyRef);

  constructor() {
    // Navigateur uniquement (pas au pré-rendu SSR).
    afterNextRender(() => {
      const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
      let lenis: Lenis | undefined;

      if (!reduce) {
        // Défilement à inertie (momentum).
        lenis = new Lenis({
          duration: 1.1,
          easing: (t) => 1 - Math.pow(1 - t, 3), // easeOutCubic
          smoothWheel: true,
        });

        let rafId = 0;
        const raf = (time: number) => {
          lenis!.raf(time);
          rafId = requestAnimationFrame(raf);
        };
        rafId = requestAnimationFrame(raf);
        this.destroyRef.onDestroy(() => {
          cancelAnimationFrame(rafId);
          lenis!.destroy();
        });
      }

      // À chaque navigation : ancre (#features) ou retour en haut.
      const sub = this.router.events
        .pipe(filter((e) => e instanceof NavigationEnd))
        .subscribe(() => {
          const fragment = this.router.parseUrl(this.router.url).fragment;
          const el = fragment ? document.getElementById(fragment) : null;

          if (lenis) {
            lenis.scrollTo(el ?? 0, { offset: el ? -70 : 0 });
          } else if (el) {
            el.scrollIntoView({ behavior: 'smooth' });
          } else {
            scrollTo({ top: 0, behavior: 'smooth' });
          }
        });
      this.destroyRef.onDestroy(() => sub.unsubscribe());
    });
  }
}
