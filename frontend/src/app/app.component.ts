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
          <div class="brand-mark">AI</div>
          <div>
            <h1>AI Virtual World</h1>
            <p>Research operations cockpit</p>
          </div>
        </div>

        <nav class="app-nav" aria-label="Primary navigation">
          <a routerLink="/copilot" routerLinkActive="active">Copilot</a>
          <a routerLink="/data-analytics" routerLinkActive="active">Analytics</a>
          <a routerLink="/projects" routerLinkActive="active">Hub</a>
          <a routerLink="/dashboard" routerLinkActive="active" [routerLinkActiveOptions]="{ exact: true }">Ops</a>
          <a routerLink="/training" routerLinkActive="active">Training</a>
          <a routerLink="/visualization" routerLinkActive="active">Visual</a>
          <a routerLink="/comparison" routerLinkActive="active">Compare</a>
          <a routerLink="/iot-ai" routerLinkActive="active">IoT</a>
          <a routerLink="/biometric-ai" routerLinkActive="active">Biometric</a>
          <a routerLink="/export-import" routerLinkActive="active">Models</a>
        </nav>

        <div class="system-pill">
          <span></span>
          API Ready
        </div>
      </header>

      <main class="app-main">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      background:
        radial-gradient(circle at top left, rgba(20, 184, 166, 0.26), transparent 32rem),
        radial-gradient(circle at 75% 10%, rgba(99, 102, 241, 0.24), transparent 28rem),
        linear-gradient(135deg, #0f172a 0%, #164e63 46%, #1f2937 100%);
    }

    .app-header {
      background: rgba(15, 23, 42, 0.76);
      backdrop-filter: blur(18px);
      padding: 1rem 1.5rem;
      color: white;
      border-bottom: 1px solid rgba(148, 163, 184, 0.22);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
      position: sticky;
      top: 0;
      z-index: 10;
      box-shadow: 0 14px 40px rgba(15, 23, 42, 0.24);
    }

    .brand-block {
      min-width: 240px;
      display: flex;
      align-items: center;
      gap: 0.85rem;
    }

    .brand-mark {
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: grid;
      place-items: center;
      background: linear-gradient(135deg, #22c55e, #06b6d4);
      color: #052e16;
      font-weight: 900;
      letter-spacing: 0.04em;
      box-shadow: 0 10px 24px rgba(6, 182, 212, 0.26);
    }

    .app-header h1 {
      margin: 0;
      font-size: 1.16rem;
      font-weight: 800;
      letter-spacing: 0;
    }

    .app-header p {
      margin: 0.2rem 0 0 0;
      color: #a7f3d0;
      font-size: 0.82rem;
    }

    .app-nav {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.35rem;
      flex-wrap: wrap;
      flex: 1;
    }

    .app-nav a {
      color: #cbd5e1;
      text-decoration: none;
      padding: 0.68rem 0.85rem;
      border-radius: 8px;
      border: 1px solid transparent;
      transition: background 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
      font-size: 0.92rem;
      font-weight: 700;
      line-height: 1;
    }

    .app-nav a:hover,
    .app-nav a.active {
      background: rgba(255, 255, 255, 0.12);
      border-color: rgba(45, 212, 191, 0.38);
      color: white;
      transform: translateY(-1px);
    }

    .system-pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      min-width: 112px;
      border: 1px solid rgba(34, 197, 94, 0.34);
      border-radius: 999px;
      color: #bbf7d0;
      background: rgba(22, 101, 52, 0.22);
      padding: 0.55rem 0.8rem;
      font-size: 0.82rem;
      font-weight: 800;
      white-space: nowrap;
    }

    .system-pill span {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #22c55e;
      box-shadow: 0 0 0 5px rgba(34, 197, 94, 0.14);
    }

    .app-main {
      padding: 1.25rem;
    }

    @media (max-width: 980px) {
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
        flex: 1 1 120px;
        text-align: center;
      }

      .system-pill {
        align-self: flex-start;
      }

      .app-main {
        padding: 0.75rem;
      }
    }
  `]
})
export class AppComponent {
  title = 'AI Dashboard';
}
