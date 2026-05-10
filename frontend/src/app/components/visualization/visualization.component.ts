import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { WebsocketService } from '../../services/websocket.service';
import { Subscription } from 'rxjs';

interface Agent {
  id: number;
  x: number;
  y: number;
  energy: number;
  reward: number;
  alive: boolean;
  color: string;
}

interface WorldState {
  agents: Agent[];
  foods: { x: number; y: number }[];
  hazards: { x: number; y: number }[];
  obstacles: { x: number; y: number }[];
  episode: number;
  step: number;
}

@Component({
  selector: 'app-visualization',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './visualization.component.html',
  styleUrls: ['./visualization.component.scss']
})
export class VisualizationComponent implements OnInit, OnDestroy {
  @ViewChild('canvas', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;
  
  private ctx!: CanvasRenderingContext2D;
  private subscription?: Subscription;
  private animationId?: number;
  
  worldState: WorldState | null = null;
  isConnected = false;
  isPaused = false;
  showSensors = false;
  showTrails = true;
  
  // Canvas settings
  private readonly CELL_SIZE = 20;
  private readonly WORLD_WIDTH = 30;
  private readonly WORLD_HEIGHT = 30;
  
  // Agent trails
  private trails: Map<number, { x: number; y: number }[]> = new Map();
  private readonly MAX_TRAIL_LENGTH = 50;

  constructor(private wsService: WebsocketService) {}

  ngOnInit(): void {
    this.initCanvas();
    this.connectWebSocket();
    this.startAnimation();
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
  }

  private initCanvas(): void {
    const canvas = this.canvasRef.nativeElement;
    canvas.width = this.WORLD_WIDTH * this.CELL_SIZE;
    canvas.height = this.WORLD_HEIGHT * this.CELL_SIZE;
    
    const context = canvas.getContext('2d');
    if (context) {
      this.ctx = context;
    }
  }

  private connectWebSocket(): void {
    this.subscription = this.wsService.connect('ws://localhost:8000/ws/training').subscribe({
      next: (data: any) => {
        this.isConnected = true;
        if (data.type === 'world_state') {
          this.worldState = data.state;
          this.updateTrails();
        }
      },
      error: (error) => {
        console.error('WebSocket error:', error);
        this.isConnected = false;
      }
    });
  }

  private updateTrails(): void {
    if (!this.worldState) return;
    
    this.worldState.agents.forEach(agent => {
      if (!this.trails.has(agent.id)) {
        this.trails.set(agent.id, []);
      }
      
      const trail = this.trails.get(agent.id)!;
      trail.push({ x: agent.x, y: agent.y });
      
      if (trail.length > this.MAX_TRAIL_LENGTH) {
        trail.shift();
      }
    });
  }

  private startAnimation(): void {
    const animate = () => {
      if (!this.isPaused) {
        this.render();
      }
      this.animationId = requestAnimationFrame(animate);
    };
    animate();
  }

  private render(): void {
    if (!this.ctx || !this.worldState) return;
    
    // Clear canvas
    this.ctx.fillStyle = '#1a1a2e';
    this.ctx.fillRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
    
    // Draw grid
    this.drawGrid();
    
    // Draw trails
    if (this.showTrails) {
      this.drawTrails();
    }
    
    // Draw obstacles
    this.drawObstacles();
    
    // Draw foods
    this.drawFoods();
    
    // Draw hazards
    this.drawHazards();
    
    // Draw agents
    this.drawAgents();
    
    // Draw sensors
    if (this.showSensors) {
      this.drawSensors();
    }
    
    // Draw info
    this.drawInfo();
  }

  private drawGrid(): void {
    this.ctx.strokeStyle = '#2a2a3e';
    this.ctx.lineWidth = 0.5;
    
    for (let x = 0; x <= this.WORLD_WIDTH; x++) {
      this.ctx.beginPath();
      this.ctx.moveTo(x * this.CELL_SIZE, 0);
      this.ctx.lineTo(x * this.CELL_SIZE, this.ctx.canvas.height);
      this.ctx.stroke();
    }
    
    for (let y = 0; y <= this.WORLD_HEIGHT; y++) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, y * this.CELL_SIZE);
      this.ctx.lineTo(this.ctx.canvas.width, y * this.CELL_SIZE);
      this.ctx.stroke();
    }
  }

  private drawTrails(): void {
    this.trails.forEach((trail, agentId) => {
      const agent = this.worldState?.agents.find(a => a.id === agentId);
      if (!agent) return;
      
      this.ctx.strokeStyle = agent.color;
      this.ctx.lineWidth = 2;
      this.ctx.globalAlpha = 0.3;
      
      this.ctx.beginPath();
      trail.forEach((pos, i) => {
        const x = pos.x * this.CELL_SIZE + this.CELL_SIZE / 2;
        const y = pos.y * this.CELL_SIZE + this.CELL_SIZE / 2;
        
        if (i === 0) {
          this.ctx.moveTo(x, y);
        } else {
          this.ctx.lineTo(x, y);
        }
      });
      this.ctx.stroke();
      
      this.ctx.globalAlpha = 1.0;
    });
  }

  private drawObstacles(): void {
    if (!this.worldState) return;
    
    this.ctx.fillStyle = '#555';
    this.worldState.obstacles.forEach(obs => {
      this.ctx.fillRect(
        obs.x * this.CELL_SIZE,
        obs.y * this.CELL_SIZE,
        this.CELL_SIZE,
        this.CELL_SIZE
      );
    });
  }

  private drawFoods(): void {
    if (!this.worldState) return;
    
    this.ctx.fillStyle = '#4CAF50';
    this.worldState.foods.forEach(food => {
      const x = food.x * this.CELL_SIZE + this.CELL_SIZE / 2;
      const y = food.y * this.CELL_SIZE + this.CELL_SIZE / 2;
      
      this.ctx.beginPath();
      this.ctx.arc(x, y, this.CELL_SIZE / 3, 0, Math.PI * 2);
      this.ctx.fill();
    });
  }

  private drawHazards(): void {
    if (!this.worldState) return;
    
    this.ctx.fillStyle = '#f44336';
    this.worldState.hazards.forEach(hazard => {
      const x = hazard.x * this.CELL_SIZE + this.CELL_SIZE / 2;
      const y = hazard.y * this.CELL_SIZE + this.CELL_SIZE / 2;
      
      this.ctx.beginPath();
      this.ctx.moveTo(x, y - this.CELL_SIZE / 3);
      this.ctx.lineTo(x + this.CELL_SIZE / 3, y + this.CELL_SIZE / 3);
      this.ctx.lineTo(x - this.CELL_SIZE / 3, y + this.CELL_SIZE / 3);
      this.ctx.closePath();
      this.ctx.fill();
    });
  }

  private drawAgents(): void {
    if (!this.worldState) return;
    
    this.worldState.agents.forEach(agent => {
      if (!agent.alive) return;
      
      const x = agent.x * this.CELL_SIZE + this.CELL_SIZE / 2;
      const y = agent.y * this.CELL_SIZE + this.CELL_SIZE / 2;
      
      // Draw agent body
      this.ctx.fillStyle = agent.color;
      this.ctx.beginPath();
      this.ctx.arc(x, y, this.CELL_SIZE / 2.5, 0, Math.PI * 2);
      this.ctx.fill();
      
      // Draw energy bar
      const barWidth = this.CELL_SIZE;
      const barHeight = 3;
      const barX = x - barWidth / 2;
      const barY = y - this.CELL_SIZE / 2 - 5;
      
      this.ctx.fillStyle = '#333';
      this.ctx.fillRect(barX, barY, barWidth, barHeight);
      
      this.ctx.fillStyle = agent.energy > 50 ? '#4CAF50' : agent.energy > 25 ? '#FFC107' : '#f44336';
      this.ctx.fillRect(barX, barY, barWidth * (agent.energy / 100), barHeight);
    });
  }

  private drawSensors(): void {
    if (!this.worldState) return;
    
    const directions = [
      [-1, -1], [0, -1], [1, -1],
      [-1, 0],           [1, 0],
      [-1, 1],  [0, 1],  [1, 1]
    ];
    
    this.ctx.strokeStyle = '#FFD700';
    this.ctx.lineWidth = 1;
    this.ctx.globalAlpha = 0.5;
    
    this.worldState.agents.forEach(agent => {
      if (!agent.alive) return;
      
      const x = agent.x * this.CELL_SIZE + this.CELL_SIZE / 2;
      const y = agent.y * this.CELL_SIZE + this.CELL_SIZE / 2;
      
      directions.forEach(([dx, dy]) => {
        this.ctx.beginPath();
        this.ctx.moveTo(x, y);
        this.ctx.lineTo(
          x + dx * this.CELL_SIZE * 3,
          y + dy * this.CELL_SIZE * 3
        );
        this.ctx.stroke();
      });
    });
    
    this.ctx.globalAlpha = 1.0;
  }

  private drawInfo(): void {
    if (!this.worldState) return;
    
    this.ctx.fillStyle = '#fff';
    this.ctx.font = '14px monospace';
    this.ctx.fillText(`Episode: ${this.worldState.episode}`, 10, 20);
    this.ctx.fillText(`Step: ${this.worldState.step}`, 10, 40);
    
    const aliveAgents = this.worldState.agents.filter(a => a.alive).length;
    this.ctx.fillText(`Alive: ${aliveAgents}/${this.worldState.agents.length}`, 10, 60);
  }

  togglePause(): void {
    this.isPaused = !this.isPaused;
  }

  toggleSensors(): void {
    this.showSensors = !this.showSensors;
  }

  toggleTrails(): void {
    this.showTrails = !this.showTrails;
  }

  clearTrails(): void {
    this.trails.clear();
  }

  resetView(): void {
    this.clearTrails();
    this.isPaused = false;
    this.showSensors = false;
    this.showTrails = true;
  }
}
