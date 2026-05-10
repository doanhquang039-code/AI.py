import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <div class="app-container">
      <header class="app-header">
        <h1>🤖 AI Training Dashboard</h1>
        <p>Powered by Angular + Python FastAPI</p>
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
      padding: 2rem;
      text-align: center;
      color: white;
      border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .app-header h1 {
      margin: 0;
      font-size: 2.5rem;
      font-weight: bold;
    }
    
    .app-header p {
      margin: 0.5rem 0 0 0;
      opacity: 0.9;
    }
    
    .app-main {
      padding: 2rem;
    }
  `]
})
export class AppComponent {
  title = 'AI Dashboard';
}
