import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ReleaseService } from '../../services/release.service';
import { Release } from '../../models/release';

@Component({
  selector: 'app-landing',
  imports: [RouterLink],
  templateUrl: './landing.html',
})
export class Landing {
  private releases = inject(ReleaseService);
  latest = signal<Release | null>(null);

  constructor() {
    this.releases.getLatest().subscribe((r) => this.latest.set(r));
  }
}
