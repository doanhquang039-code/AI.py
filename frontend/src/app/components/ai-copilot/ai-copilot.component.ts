import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

interface CopilotRecommendation {
  title: string;
  area: string;
  priority: string;
  action: string;
}

interface CopilotBriefing {
  readiness: number;
  signals: Record<string, number>;
  risks: string[];
  recommendations: CopilotRecommendation[];
  generated_at: string;
}

interface CopilotAnswer {
  answer: string;
  focus: string;
  next_steps: string[];
  confidence: number;
  generated_at: string;
}

@Component({
  selector: 'app-ai-copilot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="copilot-container">
      <div class="page-heading">
        <div>
          <h2>AI Copilot</h2>
          <p>Operational advisor for training, model registry, IoT AI, and biometric identity workflows.</p>
        </div>
        <button class="btn btn-secondary" type="button" (click)="loadBriefing()" [disabled]="loading">
          {{loading ? 'Refreshing...' : 'Refresh Briefing'}}
        </button>
      </div>

      <div class="hero-panel" *ngIf="briefing">
        <div>
          <label>AI readiness</label>
          <strong>{{briefing.readiness | number:'1.0-1'}}%</strong>
          <p>Generated {{briefing.generated_at | date:'shortTime'}}</p>
        </div>
        <div class="readiness-meter">
          <span [style.width.%]="briefing.readiness"></span>
        </div>
      </div>

      <div class="signal-grid" *ngIf="briefing">
        <article class="signal-card" *ngFor="let signal of signalEntries()">
          <label>{{formatLabel(signal[0])}}</label>
          <strong>{{signal[1] | number:'1.0-3'}}</strong>
        </article>
      </div>

      <div class="workspace-grid">
        <section class="panel">
          <div class="panel-header">
            <h3>Risks</h3>
            <span>{{briefing?.risks?.length || 0}} open</span>
          </div>
          <div class="risk-list" *ngIf="briefing?.risks?.length; else noRisks">
            <article class="risk-row" *ngFor="let risk of briefing?.risks">
              <span></span>
              <p>{{risk}}</p>
            </article>
          </div>
          <ng-template #noRisks>
            <div class="empty-state">No major risks detected.</div>
          </ng-template>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h3>Recommended Actions</h3>
            <span>{{briefing?.recommendations?.length || 0}} actions</span>
          </div>
          <div class="recommendation-list">
            <article class="recommendation-card" *ngFor="let item of briefing?.recommendations">
              <div class="rec-topline">
                <strong>{{item.title}}</strong>
                <span [class]="'priority ' + item.priority">{{item.priority}}</span>
              </div>
              <small>{{item.area}}</small>
              <p>{{item.action}}</p>
            </article>
          </div>
        </section>
      </div>

      <section class="panel ask-panel">
        <div class="panel-header">
          <h3>Ask Copilot</h3>
          <span *ngIf="answer">Confidence {{answer.confidence | percent:'1.0-0'}}</span>
        </div>

        <form class="ask-form" (ngSubmit)="ask()">
          <select name="focus" [(ngModel)]="focus">
            <option value="overview">Overview</option>
            <option value="training">Training</option>
            <option value="biometric">Biometric</option>
            <option value="iot">IoT AI</option>
          </select>
          <input name="question" [(ngModel)]="question" placeholder="Hỏi ví dụ: nên build tiếp phần biometric thế nào?">
          <button class="btn btn-primary" type="submit" [disabled]="asking || !question.trim()">
            {{asking ? 'Thinking...' : 'Ask'}}
          </button>
        </form>

        <div class="answer-card" *ngIf="answer">
          <p>{{answer.answer}}</p>
          <div class="next-steps">
            <span *ngFor="let step of answer.next_steps">{{step}}</span>
          </div>
        </div>
      </section>

      <div class="error" *ngIf="error">{{error}}</div>
    </div>
  `,
  styles: [`
    .copilot-container {
      color: white;
      margin: 0 auto;
      max-width: 1400px;
      padding: 2rem;
    }

    .page-heading,
    .panel-header,
    .rec-topline {
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
    .hero-panel p,
    .recommendation-card small,
    .empty-state {
      color: rgba(255, 255, 255, 0.72);
    }

    .hero-panel,
    .signal-card,
    .panel {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      color: white;
    }

    .hero-panel {
      display: grid;
      grid-template-columns: 240px 1fr;
      gap: 1.5rem;
      margin-bottom: 1rem;
      padding: 1.35rem;
    }

    .hero-panel label,
    .signal-card label {
      color: rgba(255, 255, 255, 0.68);
      display: block;
      font-size: 0.85rem;
      margin-bottom: 0.4rem;
    }

    .hero-panel strong {
      display: block;
      font-size: 3rem;
      line-height: 1;
      margin-bottom: 0.45rem;
    }

    .readiness-meter {
      align-self: center;
      background: rgba(15, 23, 42, 0.42);
      border-radius: 999px;
      height: 18px;
      overflow: hidden;
    }

    .readiness-meter span {
      background: linear-gradient(90deg, #22c55e, #06b6d4);
      border-radius: inherit;
      display: block;
      height: 100%;
    }

    .signal-grid {
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .signal-card {
      min-height: 108px;
      padding: 1rem;
    }

    .signal-card strong {
      font-size: 1.55rem;
    }

    .workspace-grid {
      display: grid;
      grid-template-columns: 0.9fr 1.1fr;
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .panel {
      padding: 1.25rem;
    }

    .risk-list,
    .recommendation-list {
      display: grid;
      gap: 0.8rem;
      margin-top: 1rem;
    }

    .risk-row,
    .recommendation-card,
    .answer-card {
      background: rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 0.9rem;
    }

    .risk-row {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 0.75rem;
    }

    .risk-row span {
      background: #f59e0b;
      border-radius: 999px;
      box-shadow: 0 0 0 5px rgba(245, 158, 11, 0.14);
      height: 8px;
      margin-top: 0.45rem;
      width: 8px;
    }

    .recommendation-card p {
      color: rgba(255, 255, 255, 0.82);
      margin-top: 0.55rem;
    }

    .priority {
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 900;
      padding: 0.28rem 0.55rem;
      text-transform: uppercase;
    }

    .priority.high {
      background: rgba(248, 113, 113, 0.18);
      color: #fecaca;
    }

    .priority.medium {
      background: rgba(250, 204, 21, 0.16);
      color: #fde68a;
    }

    .ask-form {
      display: grid;
      grid-template-columns: 160px 1fr auto;
      gap: 0.75rem;
      margin-top: 1rem;
    }

    input,
    select {
      background: rgba(15, 23, 42, 0.42);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      color: white;
      min-height: 44px;
      padding: 0.68rem 0.8rem;
    }

    option {
      color: #111827;
    }

    .btn {
      border: 0;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 800;
      min-height: 44px;
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

    .answer-card {
      margin-top: 1rem;
    }

    .next-steps {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 0.9rem;
    }

    .next-steps span {
      background: rgba(34, 197, 94, 0.14);
      border: 1px solid rgba(34, 197, 94, 0.22);
      border-radius: 8px;
      color: #bbf7d0;
      padding: 0.45rem 0.6rem;
    }

    .error {
      color: #fecaca;
      margin-top: 1rem;
    }

    @media (max-width: 1100px) {
      .signal-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }
    }

    @media (max-width: 820px) {
      .copilot-container {
        padding: 1rem;
      }

      .page-heading,
      .hero-panel,
      .workspace-grid,
      .ask-form {
        grid-template-columns: 1fr;
      }

      .page-heading,
      .panel-header {
        flex-direction: column;
      }

      .signal-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 520px) {
      .signal-grid {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class AiCopilotComponent implements OnInit {
  briefing: CopilotBriefing | null = null;
  answer: CopilotAnswer | null = null;
  question = 'Nên build tiếp phần AI nào để demo tốt nhất?';
  focus = 'overview';
  loading = false;
  asking = false;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadBriefing();
  }

  loadBriefing() {
    this.loading = true;
    this.error = '';
    this.api.get<CopilotBriefing>('copilot/briefing').subscribe({
      next: data => {
        this.briefing = data;
        this.loading = false;
      },
      error: err => {
        console.error(err);
        this.error = 'Failed to load AI briefing';
        this.loading = false;
      }
    });
  }

  ask() {
    this.asking = true;
    this.error = '';
    this.api.post<CopilotAnswer>('copilot/ask', {
      question: this.question,
      focus: this.focus
    }).subscribe({
      next: data => {
        this.answer = data;
        this.asking = false;
      },
      error: err => {
        console.error(err);
        this.error = 'Copilot failed to answer';
        this.asking = false;
      }
    });
  }

  signalEntries(): Array<[string, number]> {
    return Object.entries(this.briefing?.signals || {});
  }

  formatLabel(value: string): string {
    return value.replace(/_/g, ' ');
  }
}
