import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ReleaseService } from '../../services/release.service';
import { Release } from '../../models/release';

@Component({
  selector: 'app-download',
  imports: [DatePipe],
  templateUrl: './download.html',
})
export class Download {
  private service = inject(ReleaseService);

  releases = signal<Release[]>([]);
  loading = signal(true);

  latest = computed(() => this.releases()[0] ?? null);
  history = computed(() => this.releases().slice(1));

  constructor() {
    this.service.getReleases().subscribe((list) => {
      this.releases.set(list);
      this.loading.set(false);
    });
  }

  sizeMb(bytes: number | null): string {
    if (!bytes) return '—';
    return (bytes / (1024 * 1024)).toFixed(1) + ' Mo';
  }
}
