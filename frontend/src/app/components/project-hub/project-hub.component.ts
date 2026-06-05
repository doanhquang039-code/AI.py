import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

interface ProjectTask {
  id: string;
  title: string;
  status: string;
  owner: string;
  note?: string;
  updated_at?: string;
}

interface ProjectMilestone {
  id: string;
  name: string;
  progress: number;
}

interface ProjectItem {
  id: string;
  name: string;
  summary: string;
  health: number;
  stage: string;
  capabilities: string[];
  metrics: Record<string, number>;
  milestones: ProjectMilestone[];
  tasks: ProjectTask[];
  task_summary: {
    total: number;
    done: number;
    active: number;
    next: number;
  };
}

@Component({
  selector: 'app-project-hub',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="hub-container">
      <div class="page-heading">
        <div>
          <h2>Project Hub</h2>
          <p>Two large workstreams: AI Core Platform and IoT AI Operations.</p>
        </div>
        <button class="btn btn-secondary" type="button" (click)="loadProjects()" [disabled]="loading">
          {{loading ? 'Refreshing...' : 'Refresh'}}
        </button>
      </div>

      <div class="project-grid">
        <button
          class="project-card"
          type="button"
          *ngFor="let project of projects"
          [class.selected]="selectedProject?.id === project.id"
          (click)="selectProject(project)">
          <div class="project-topline">
            <strong>{{project.name}}</strong>
            <span>{{project.stage}}</span>
          </div>
          <p>{{project.summary}}</p>
          <div class="health-row">
            <label>Health</label>
            <strong>{{project.health | number:'1.1-1'}}%</strong>
          </div>
          <progress [value]="project.health" max="100"></progress>
          <div class="task-strip">
            <span>{{project.task_summary.active}} active</span>
            <span>{{project.task_summary.next}} next</span>
            <span>{{project.task_summary.done}} done</span>
          </div>
        </button>
      </div>

      <div class="project-detail" *ngIf="selectedProject">
        <section class="panel">
          <div class="panel-header">
            <h3>{{selectedProject.name}} Metrics</h3>
            <span>{{selectedProject.task_summary.total}} tasks</span>
          </div>

          <div class="metric-grid">
            <div class="metric-card" *ngFor="let metric of selectedProject.metrics | keyvalue">
              <label>{{formatLabel(metric.key)}}</label>
              <strong>{{metric.value}}</strong>
            </div>
          </div>

          <div class="capabilities">
            <span *ngFor="let capability of selectedProject.capabilities">{{capability}}</span>
          </div>
        </section>

        <section class="panel">
          <div class="panel-header">
            <h3>Milestones</h3>
            <span>Roadmap progress</span>
          </div>

          <div class="milestone-list">
            <div class="milestone" *ngFor="let milestone of selectedProject.milestones">
              <div>
                <strong>{{milestone.name}}</strong>
                <span>{{milestone.progress}}%</span>
              </div>
              <progress [value]="milestone.progress" max="100"></progress>
            </div>
          </div>
        </section>
      </div>

      <section class="panel task-panel" *ngIf="selectedProject">
        <div class="panel-header">
          <h3>Task Board</h3>
          <span>{{selectedProject.name}}</span>
        </div>

        <div class="task-board">
          <article class="task-card" *ngFor="let task of selectedProject.tasks">
            <div class="task-topline">
              <span [class]="'status ' + task.status">{{task.status}}</span>
              <small>{{task.owner}}</small>
            </div>
            <h4>{{task.title}}</h4>
            <p *ngIf="task.note">{{task.note}}</p>
            <div class="task-actions">
              <button class="btn btn-secondary" type="button" (click)="updateTask(task, 'active')">Active</button>
              <button class="btn btn-primary" type="button" (click)="updateTask(task, 'done')">Done</button>
            </div>
          </article>
        </div>
      </section>

      <div class="error" *ngIf="error">{{error}}</div>
    </div>
  `,
  styles: [`
    .hub-container {
      color: white;
      margin: 0 auto;
      max-width: 1400px;
      padding: 2rem;
    }

    .page-heading,
    .project-topline,
    .panel-header,
    .health-row,
    .milestone div,
    .task-topline,
    .task-actions {
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
    h4,
    p {
      margin: 0;
    }

    .page-heading p,
    .project-card p,
    .panel-header span,
    .milestone span,
    .task-card small,
    .task-card p {
      color: rgba(255, 255, 255, 0.72);
    }

    .project-grid,
    .project-detail {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }

    .project-card,
    .panel,
    .task-card {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      color: white;
    }

    .project-card {
      cursor: pointer;
      padding: 1.25rem;
      text-align: left;
    }

    .project-card.selected,
    .project-card:hover {
      background: rgba(255, 255, 255, 0.17);
    }

    .project-topline span,
    .task-strip span,
    .capabilities span,
    .status {
      background: rgba(255, 255, 255, 0.14);
      border-radius: 8px;
      padding: 0.35rem 0.5rem;
    }

    .health-row {
      margin-top: 1rem;
    }

    progress {
      width: 100%;
      height: 10px;
      accent-color: #22c55e;
    }

    .task-strip,
    .capabilities {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    .panel {
      padding: 1.25rem;
    }

    .metric-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 0.75rem;
      margin: 1rem 0;
    }

    .metric-card,
    .milestone,
    .task-card {
      background: rgba(255, 255, 255, 0.06);
      border-radius: 8px;
      padding: 0.85rem;
    }

    .metric-card label {
      display: block;
      color: rgba(255, 255, 255, 0.68);
      font-size: 0.82rem;
      margin-bottom: 0.35rem;
    }

    .metric-card strong {
      font-size: 1.25rem;
    }

    .milestone-list,
    .task-board {
      display: grid;
      gap: 0.75rem;
    }

    .task-board {
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    }

    .task-panel {
      margin-bottom: 1rem;
    }

    .task-card h4 {
      margin: 0.85rem 0;
    }

    .status.done {
      color: #bbf7d0;
    }

    .status.active {
      color: #bfdbfe;
    }

    .status.next {
      color: #fde68a;
    }

    .btn {
      border: 0;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 700;
      padding: 0.65rem 0.85rem;
    }

    .btn-primary {
      background: #22c55e;
      color: #052e16;
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.18);
      color: white;
    }

    .error {
      color: #fecaca;
    }

    @media (max-width: 900px) {
      .hub-container {
        padding: 1rem;
      }

      .page-heading,
      .project-grid,
      .project-detail,
      .metric-grid {
        grid-template-columns: 1fr;
      }

      .page-heading,
      .panel-header,
      .task-actions {
        flex-direction: column;
      }
    }
  `]
})
export class ProjectHubComponent implements OnInit {
  projects: ProjectItem[] = [];
  selectedProject: ProjectItem | null = null;
  loading = false;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadProjects();
  }

  loadProjects() {
    this.loading = true;
    this.error = '';
    this.api.get<{ projects: ProjectItem[] }>('projects').subscribe({
      next: (data) => {
        this.projects = data.projects;
        this.selectedProject = this.selectedProject
          ? this.projects.find((project) => project.id === this.selectedProject?.id) || this.projects[0]
          : this.projects[0];
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load project hub:', err);
        this.error = 'Failed to load project hub';
        this.loading = false;
      }
    });
  }

  selectProject(project: ProjectItem) {
    this.selectedProject = project;
  }

  updateTask(task: ProjectTask, status: string) {
    if (!this.selectedProject) {
      return;
    }

    this.api.patch<{ status: string }>(
      `projects/${this.selectedProject.id}/tasks/${task.id}`,
      { status, owner: task.owner, note: `Marked ${status} from Project Hub` }
    ).subscribe({
      next: () => this.loadProjects(),
      error: (err) => {
        console.error('Failed to update task:', err);
        this.error = 'Failed to update task';
      }
    });
  }

  formatLabel(value: string): string {
    return value.replace(/_/g, ' ');
  }
}
