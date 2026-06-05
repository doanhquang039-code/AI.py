import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="app-container">
      <header class="app-header">
        <div class="brand-block">
          <h1>AI Training Dashboard</h1>
          <p>Angular + FastAPI research workspace</p>
        </div>

        <nav class="app-nav" aria-label="Primary navigation">
          <a routerLink="/dashboard" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">Dashboard</a>
          <a routerLink="/training" routerLinkActive="active">Training</a>
          <a routerLink="/visualization" routerLinkActive="active">Visualization</a>
          <a routerLink="/comparison" routerLinkActive="active">Comparison</a>
          <a routerLink="/iot-ai" routerLinkActive="active">IoT AI</a>
          <a routerLink="/export-import" routerLinkActive="active">Export</a>
        </nav>
      </header>

      <main class="app-main">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .app-header {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      padding: 1.25rem 2rem;
      color: white;
      border-bottom: 1px solid rgba(255, 255, 255, 0.2);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1.5rem;
      position: sticky;
      top: 0;
      z-index: 10;
    }

    .brand-block {
      min-width: 220px;
    }

    .app-header h1 {
      margin: 0;
      font-size: 1.45rem;
      font-weight: bold;
    }

    .app-header p {
      margin: 0.25rem 0 0 0;
      opacity: 0.9;
      font-size: 0.92rem;
    }

    .app-nav {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .app-nav a {
      color: rgba(255, 255, 255, 0.88);
      text-decoration: none;
      padding: 0.65rem 0.85rem;
      border-radius: 8px;
      border: 1px solid transparent;
      transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease;
      font-size: 0.95rem;
      line-height: 1;
    }

    .app-nav a:hover,
    .app-nav a.active {
      background: rgba(255, 255, 255, 0.16);
      border-color: rgba(255, 255, 255, 0.22);
      color: white;
    }

    .app-main {
      padding: 2rem;
    }

    @media (max-width: 820px) {
      .app-header {
        align-items: stretch;
        flex-direction: column;
        padding: 1rem;
      }

      .brand-block {
        min-width: 0;
      }

      .app-nav {
        justify-content: flex-start;
      }

      .app-nav a {
        flex: 1 1 130px;
        text-align: center;
      }

      .app-main {
        padding: 1rem;
      }
    }
  `]
})
export class AppComponent {
  title = 'AI Dashboard';
}
