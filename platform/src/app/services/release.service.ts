import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, catchError, of } from 'rxjs';
import { environment } from '../../environments/environment';
import { Release } from '../models/release';

@Injectable({ providedIn: 'root' })
export class ReleaseService {
  private http = inject(HttpClient);
  private base = environment.apiBase;

  /** Toutes les versions publiées (plus récente d'abord). */
  getReleases(): Observable<Release[]> {
    return this.http
      .get<Release[]>(`${this.base}/api/releases`)
      .pipe(catchError(() => of([])));
  }

  /** Dernière version publiée, ou null si aucune. */
  getLatest(): Observable<Release | null> {
    return this.http
      .get<Release | null>(`${this.base}/api/releases/latest`)
      .pipe(catchError(() => of(null)));
  }
}
