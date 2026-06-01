import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { environment } from '../../environments/environment';

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket$: WebSocketSubject<WebSocketMessage> | null = null;
  private messagesSubject$ = new Subject<WebSocketMessage>();
  public messages$ = this.messagesSubject$.asObservable();
  
  private reconnectInterval = 5000; // 5 seconds
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;
  private isConnected = false;
  private wsUrl = environment.wsUrl;

  constructor() {
    this.connect();
  }

  /**
   * Connect to WebSocket server
   */
  public connect(): void {
    if (this.socket$) {
      return;
    }

    this.shouldReconnect = true;
    this.socket$ = webSocket({
      url: this.wsUrl,
      openObserver: {
        next: () => {
          console.log('✅ WebSocket connected');
          this.isConnected = true;
          this.clearReconnectTimer();
          this.sendMessage({ type: 'subscribe' });
        }
      },
      closeObserver: {
        next: () => {
          console.log('❌ WebSocket disconnected');
          this.isConnected = false;
          this.socket$ = null;
          this.scheduleReconnect();
        }
      }
    });

    this.socket$.subscribe({
      next: (message) => this.handleMessage(message),
      error: (error) => {
        console.error('WebSocket error:', error);
        this.isConnected = false;
        this.socket$ = null;
        this.scheduleReconnect();
      }
    });
  }

  /**
   * Reconnect to WebSocket server
   */
  private scheduleReconnect(): void {
    if (!this.shouldReconnect || this.reconnectTimer) {
      return;
    }

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      console.log('Attempting to reconnect...');
      this.connect();
    }, this.reconnectInterval);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WebSocketMessage): void {
    this.messagesSubject$.next(message);
  }

  /**
   * Send message to WebSocket server
   */
  public sendMessage(message: WebSocketMessage): void {
    if (this.socket$ && this.isConnected) {
      this.socket$.next(message);
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }

  /**
   * Subscribe to specific message types
   */
  public onMessageType(type: string): Observable<WebSocketMessage> {
    return new Observable(observer => {
      const subscription = this.messages$.subscribe({
        next: (message) => {
          if (message.type === type) {
            observer.next(message);
          }
        },
        error: (err) => observer.error(err),
        complete: () => observer.complete()
      });

      return () => subscription.unsubscribe();
    });
  }

  /**
   * Subscribe to training updates
   */
  public onTrainingUpdate(): Observable<WebSocketMessage> {
    return this.onMessageType('training_update');
  }

  /**
   * Subscribe to model updates
   */
  public onModelUpdate(): Observable<WebSocketMessage> {
    return this.onMessageType('model_update');
  }

  /**
   * Check if WebSocket is connected
   */
  public isSocketConnected(): boolean {
    return this.isConnected;
  }

  /**
   * Close WebSocket connection
   */
  public disconnect(): void {
    this.shouldReconnect = false;
    this.clearReconnectTimer();
    if (this.socket$) {
      this.socket$.complete();
      this.socket$ = null;
      this.isConnected = false;
    }
  }

  /**
   * Send ping to keep connection alive
   */
  public ping(): void {
    this.sendMessage({ type: 'ping' });
  }
}
