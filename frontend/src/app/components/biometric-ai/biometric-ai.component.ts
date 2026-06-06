import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

interface BiometricModality {
  id: string;
  label: string;
  threshold: number;
  signals: string[];
}

interface BiometricSummary {
  profile_count: number;
  event_count: number;
  verified_count: number;
  review_count: number;
  avg_quality: number;
  avg_match: number;
  modalities_online: number;
  risk_level: string;
  updated_at: string;
}

interface BiometricProfile {
  id: string;
  identity_id: string;
  display_name: string;
  modality: string;
  template_hash: string;
  quality_score: number;
  sample_size: number;
  status: string;
  enrolled_at: string;
}

interface BiometricEvent {
  id: string;
  identity_id: string;
  modality: string;
  type: string;
  match_score: number;
  threshold?: number;
  liveness_score?: number;
  decision: string;
  created_at: string;
}

@Component({
  selector: 'app-biometric-ai',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="bio-container">
      <div class="page-heading">
        <div>
          <h2>Biometric AI Center</h2>
          <p>Face, fingerprint, voice, and palm-vein recognition workflow with privacy-first metadata.</p>
        </div>
        <button class="btn btn-secondary" type="button" (click)="loadData()" [disabled]="loading">
          {{loading ? 'Refreshing...' : 'Refresh'}}
        </button>
      </div>

      <div class="summary-grid" *ngIf="summary">
        <div class="summary-card">
          <label>Profiles</label>
          <strong>{{summary.profile_count}}</strong>
          <span>{{summary.modalities_online}} modalities online</span>
        </div>
        <div class="summary-card">
          <label>Avg Quality</label>
          <strong>{{summary.avg_quality | percent:'1.0-1'}}</strong>
          <span>Enrollment signal quality</span>
        </div>
        <div class="summary-card">
          <label>Verified</label>
          <strong>{{summary.verified_count}}</strong>
          <span>{{summary.review_count}} sent to review</span>
        </div>
        <div class="summary-card">
          <label>Risk</label>
          <strong>{{summary.risk_level}}</strong>
          <span>{{summary.event_count}} audit events</span>
        </div>
      </div>

      <div class="workspace-grid">
        <section class="panel enroll-panel">
          <div class="panel-header">
            <h3>Enroll Identity</h3>
            <span>Raw sample is not persisted</span>
          </div>

          <form class="form-grid" (ngSubmit)="enroll()">
            <label>
              Identity ID
              <input name="identityId" [(ngModel)]="identityId" required placeholder="EMP-1024">
            </label>
            <label>
              Display Name
              <input name="displayName" [(ngModel)]="displayName" placeholder="Nguyen Van A">
            </label>
            <label>
              Modality
              <select name="selectedModality" [(ngModel)]="selectedModality">
                <option *ngFor="let modality of modalities" [value]="modality.id">{{modality.label}}</option>
              </select>
            </label>
            <label>
              Sample
              <input type="file" (change)="selectFile($event)" accept="image/*,audio/*,.bin,.dat">
            </label>

            <button class="btn btn-primary" type="submit" [disabled]="busy || !identityId">
              {{busy ? 'Processing...' : 'Enroll Sample'}}
            </button>
          </form>

          <div class="privacy-note">
            <strong>Privacy guard</strong>
            <p>Demo API extracts a template hash and quality score, then discards the uploaded bytes.</p>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h3>Verification Console</h3>
            <span>Threshold based decision</span>
          </div>

          <div class="verify-grid">
            <label>
              Identity
              <select [(ngModel)]="verifyIdentity" name="verifyIdentity">
                <option value="">Select profile</option>
                <option *ngFor="let profile of profiles" [value]="profile.identity_id + ':' + profile.modality">
                  {{profile.display_name}} / {{labelFor(profile.modality)}}
                </option>
              </select>
            </label>
            <label>
              Liveness
              <input type="range" min="0.3" max="1" step="0.01" [(ngModel)]="livenessScore" name="livenessScore">
              <span>{{livenessScore | number:'1.2-2'}}</span>
            </label>
            <button class="btn btn-primary" type="button" (click)="verify()" [disabled]="busy || !verifyIdentity">
              Verify Identity
            </button>
          </div>

          <div class="decision-card" *ngIf="lastEvent">
            <span [class]="'decision ' + lastEvent.decision">{{lastEvent.decision}}</span>
            <strong>{{lastEvent.match_score | percent:'1.0-1'}}</strong>
            <p>{{lastEvent.modality}} threshold {{lastEvent.threshold | percent:'1.0-1'}}</p>
          </div>
        </section>
      </div>

      <div class="workspace-grid">
        <section class="panel">
          <div class="panel-header">
            <h3>Recognition Pipelines</h3>
            <span>{{modalities.length}} active</span>
          </div>
          <div class="modality-list">
            <article class="modality-card" *ngFor="let modality of modalities">
              <div>
                <strong>{{modality.label}}</strong>
                <span>{{modality.threshold | percent:'1.0-0'}} threshold</span>
              </div>
              <div class="signal-list">
                <small *ngFor="let signal of modality.signals">{{signal}}</small>
              </div>
            </article>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h3>Enrolled Profiles</h3>
            <span>{{profiles.length}} templates</span>
          </div>
          <div class="profile-list" *ngIf="profiles.length > 0; else emptyProfiles">
            <article class="profile-row" *ngFor="let profile of profiles.slice(0, 8)">
              <div>
                <strong>{{profile.display_name}}</strong>
                <span>{{profile.identity_id}} / {{labelFor(profile.modality)}}</span>
              </div>
              <div class="quality">
                <strong>{{profile.quality_score | percent:'1.0-1'}}</strong>
                <small>{{profile.status}}</small>
              </div>
            </article>
          </div>
          <ng-template #emptyProfiles>
            <div class="empty-state">No biometric profiles enrolled yet.</div>
          </ng-template>
        </section>
      </div>

      <section class="panel">
        <div class="panel-header">
          <h3>Audit Trail</h3>
          <span>{{events.length}} recent events</span>
        </div>
        <div class="audit-table">
          <div class="audit-row head">
            <span>Event</span>
            <span>Identity</span>
            <span>Modality</span>
            <span>Score</span>
            <span>Decision</span>
          </div>
          <div class="audit-row" *ngFor="let event of events.slice(0, 10)">
            <span>{{event.type}}</span>
            <span>{{event.identity_id}}</span>
            <span>{{labelFor(event.modality)}}</span>
            <span>{{event.match_score | percent:'1.0-1'}}</span>
            <span [class]="'decision ' + event.decision">{{event.decision}}</span>
          </div>
        </div>
      </section>

      <div class="error" *ngIf="error">{{error}}</div>
    </div>
  `,
  styles: [`
    .bio-container {
      color: white;
      margin: 0 auto;
      max-width: 1440px;
      padding: 2rem;
    }

    .page-heading,
    .panel-header,
    .profile-row,
    .modality-card > div:first-child {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 1rem;
    }

    .page-heading {
      margin-bottom: 1.5rem;
    }

    h2,
    h3,
    p {
      margin: 0;
    }

    .page-heading p,
    .panel-header span,
    .summary-card span,
    .profile-row span,
    .quality small,
    .modality-card span {
      color: rgba(255, 255, 255, 0.72);
    }

    .summary-grid,
    .workspace-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .workspace-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .summary-card,
    .panel {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      color: white;
    }

    .summary-card {
      min-height: 128px;
      padding: 1.2rem;
    }

    .summary-card label {
      color: rgba(255, 255, 255, 0.68);
      display: block;
      font-size: 0.84rem;
      margin-bottom: 0.45rem;
    }

    .summary-card strong {
      display: block;
      font-size: 2rem;
      line-height: 1.05;
      margin-bottom: 0.4rem;
      text-transform: capitalize;
    }

    .panel {
      padding: 1.25rem;
    }

    .form-grid,
    .verify-grid,
    .profile-list,
    .modality-list {
      display: grid;
      gap: 0.85rem;
      margin-top: 1rem;
    }

    .form-grid {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    label {
      color: rgba(255, 255, 255, 0.78);
      display: grid;
      font-size: 0.86rem;
      gap: 0.45rem;
    }

    input,
    select {
      background: rgba(15, 23, 42, 0.42);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      color: white;
      min-height: 42px;
      padding: 0.65rem 0.75rem;
      width: 100%;
    }

    input[type="file"] {
      padding: 0.52rem;
    }

    option {
      color: #111827;
    }

    .btn {
      border: 0;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 800;
      min-height: 42px;
      padding: 0.72rem 1rem;
    }

    .btn-primary {
      background: #22c55e;
      color: #052e16;
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.18);
      color: white;
    }

    .btn:disabled {
      cursor: not-allowed;
      opacity: 0.6;
    }

    .privacy-note,
    .decision-card,
    .profile-row,
    .modality-card {
      background: rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 0.9rem;
    }

    .privacy-note {
      margin-top: 1rem;
    }

    .privacy-note p {
      color: rgba(255, 255, 255, 0.72);
      margin-top: 0.35rem;
    }

    .decision-card {
      margin-top: 1rem;
      text-align: center;
    }

    .decision-card strong {
      display: block;
      font-size: 2.4rem;
      margin: 0.45rem 0;
    }

    .decision {
      background: rgba(255, 255, 255, 0.14);
      border-radius: 999px;
      display: inline-flex;
      font-size: 0.78rem;
      font-weight: 900;
      padding: 0.3rem 0.55rem;
      text-transform: uppercase;
    }

    .decision.verified,
    .decision.ready {
      color: #bbf7d0;
    }

    .decision.review,
    .decision.needs_retake {
      color: #fde68a;
    }

    .signal-list {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 0.8rem;
    }

    .signal-list small {
      background: rgba(255, 255, 255, 0.12);
      border-radius: 8px;
      padding: 0.35rem 0.5rem;
    }

    .quality {
      text-align: right;
    }

    .audit-table {
      display: grid;
      gap: 0.45rem;
      margin-top: 1rem;
    }

    .audit-row {
      align-items: center;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      display: grid;
      gap: 0.75rem;
      grid-template-columns: 1fr 1fr 1.1fr 0.7fr 0.9fr;
      padding: 0.75rem;
    }

    .audit-row.head {
      background: transparent;
      color: rgba(255, 255, 255, 0.68);
      font-size: 0.82rem;
      font-weight: 800;
      text-transform: uppercase;
    }

    .empty-state,
    .error {
      color: rgba(255, 255, 255, 0.72);
      padding: 1rem 0;
    }

    @media (max-width: 980px) {
      .bio-container {
        padding: 1rem;
      }

      .summary-grid,
      .workspace-grid,
      .form-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 720px) {
      .page-heading,
      .panel-header,
      .profile-row {
        flex-direction: column;
      }

      .summary-grid,
      .workspace-grid,
      .form-grid,
      .audit-row {
        grid-template-columns: 1fr;
      }

      .quality {
        text-align: left;
      }
    }
  `]
})
export class BiometricAiComponent implements OnInit {
  modalities: BiometricModality[] = [];
  summary: BiometricSummary | null = null;
  profiles: BiometricProfile[] = [];
  events: BiometricEvent[] = [];
  selectedModality = 'face';
  identityId = 'EMP-1001';
  displayName = 'Demo User';
  verifyIdentity = '';
  livenessScore = 0.88;
  selectedFile: File | null = null;
  lastEvent: BiometricEvent | null = null;
  loading = false;
  busy = false;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadData();
  }

  loadData() {
    this.loading = true;
    this.error = '';
    let pending = 4;
    const finish = () => {
      pending -= 1;
      this.loading = pending > 0;
    };

    this.api.get<{ modalities: BiometricModality[] }>('biometric/modalities').subscribe({
      next: data => {
        this.modalities = data.modalities;
        if (!this.modalities.some(modality => modality.id === this.selectedModality)) {
          this.selectedModality = this.modalities[0]?.id || 'face';
        }
        finish();
      },
      error: err => {
        console.error(err);
        this.error = 'Failed to load biometric modalities';
        finish();
      }
    });

    this.api.get<BiometricSummary>('biometric/summary').subscribe({
      next: data => {
        this.summary = data;
        finish();
      },
      error: err => {
        console.error(err);
        finish();
      }
    });

    this.api.get<{ profiles: BiometricProfile[] }>('biometric/profiles').subscribe({
      next: data => {
        this.profiles = data.profiles;
        if (!this.verifyIdentity && this.profiles.length > 0) {
          const first = this.profiles[0];
          this.verifyIdentity = `${first.identity_id}:${first.modality}`;
        }
        finish();
      },
      error: err => {
        console.error(err);
        finish();
      }
    });

    this.api.get<{ events: BiometricEvent[] }>('biometric/audit').subscribe({
      next: data => {
        this.events = data.events;
        finish();
      },
      error: err => {
        console.error(err);
        finish();
      }
    });
  }

  selectFile(event: Event) {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] || null;
  }

  enroll() {
    const form = new FormData();
    form.append('identity_id', this.identityId);
    form.append('display_name', this.displayName);
    form.append('modality', this.selectedModality);
    if (this.selectedFile) {
      form.append('sample', this.selectedFile);
    }

    this.busy = true;
    this.api.postForm<BiometricProfile>('biometric/enroll', form).subscribe({
      next: profile => {
        this.busy = false;
        this.verifyIdentity = `${profile.identity_id}:${profile.modality}`;
        this.loadData();
      },
      error: err => {
        console.error(err);
        this.error = 'Enrollment failed';
        this.busy = false;
      }
    });
  }

  verify() {
    const [identityId, modality] = this.verifyIdentity.split(':');
    this.busy = true;
    this.api.post<BiometricEvent>('biometric/verify', {
      identity_id: identityId,
      modality,
      liveness_score: Number(this.livenessScore)
    }).subscribe({
      next: event => {
        this.lastEvent = event;
        this.busy = false;
        this.loadData();
      },
      error: err => {
        console.error(err);
        this.error = 'Verification failed';
        this.busy = false;
      }
    });
  }

  labelFor(modalityId: string): string {
    return this.modalities.find(modality => modality.id === modalityId)?.label || modalityId;
  }
}
