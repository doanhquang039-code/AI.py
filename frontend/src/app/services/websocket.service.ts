import { Injectable } from '@angular/core';
import { Observable, Subject, interval } from 'rxjs';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { retry, tap, delayWhen } from 'rxjs/operators';

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket$: WebSocketSubject<any> | null = null;
  private messagesSubject$ = new Subject<WebSocketMessage>();
  public messages$ = this.messagesSubject$.asObservable();
  
  private reconnectInterval = 5000; // 5 seconds
  private isConnected = false;
  private wsUrl = 'ws://localhost:8000/ws';

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

    this.socket$ = webSocket({
      url: this.wsUrl,
      openObserver: {
        next: () => {
          console.log('✅ WebSocket connected');
          this.isConnected = true;
          this.sendMessage({ type: 'subscribe' });
        }
      },
      closeObserver: {
        next: () => {
          console.log('❌ WebSocket disconnected');
          this.isConnected = false;
          this.socket$ = null;
          this.reconnect();
        }
      }
    });

    this.socket$
      .pipe(
        tap({
          error: (error) => console.error('WebSocket error:', error)
        }),
        retry({
          delay: () => {
            console.log(`Retrying connection in ${this.reconnectInterval}ms...`);
            return interval(this.reconnectInterval);
          }
        })
      )
      .subscribe({
        next: (message) => this.handleMessage(message),
        error: (error) => console.error('WebSocket subscription error:', error)
      });
  }

  /**
   * Reconnect to WebSocket server
   */
  private reconnect(): void {
    setTimeout(() => {
      console.log('Attempting to reconnect...');
      this.connect();
    }, this.reconnectInterval);
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(message: WebSocketMessage): void {
    console.log('📨 WebSocket message received:', message);
    this.messagesSubject$.next(message);
  }

  /**
   * Send message to WebSocket server
   */
  public sendMessage(message: any): void {
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
