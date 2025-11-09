export class ReconnectingWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private protocols?: string | string[];
  private reconnectAttempts = 0;
  private forcedClose = false;
  private maxAttempts = 10;
  private reconnectInterval = 1000;
  
  public onopen: ((event: Event) => void) | null = null;
  public onclose: ((event: CloseEvent) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  public onmessage: ((event: MessageEvent) => void) | null = null;
  
  constructor(url: string, protocols?: string | string[]) {
    this.url = url;
    this.protocols = protocols;
    this.connect();
  }
  
  private connect(): void {
    if (this.forcedClose) return;
    
    this.ws = new WebSocket(this.url, this.protocols);
    
    this.ws.onopen = (event) => {
      this.reconnectAttempts = 0;
      this.onopen?.(event);
    };
    
    this.ws.onclose = (event) => {
      if (!this.forcedClose && this.reconnectAttempts < this.maxAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect();
        }, this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts));
      }
      this.onclose?.(event);
    };
    
    this.ws.onerror = (event) => this.onerror?.(event);
    this.ws.onmessage = (event) => this.onmessage?.(event);
  }
  
  public send(data: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    }
  }
  
  public close(): void {
    this.forcedClose = true;
    this.ws?.close();
  }
  
  public get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }
}
