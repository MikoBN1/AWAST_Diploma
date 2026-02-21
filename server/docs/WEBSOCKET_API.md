# Real-Time Scan Monitoring via WebSocket

The backend provides a WebSocket endpoint that allows clients to monitor the progress of an active ZAP scan and receive vulnerabilities (alerts) dynamically as they are discovered.

## Endpoint

```
WS /api/v1/zap/ws/scan/{scan_id}
```

- **Method:** `WebSocket`
- **Path Parameter:** `scan_id` (string) - The UUID of the scan returned by the `POST /api/v1/zap/scan` endpoint.

## Connection Lifecycle

1. **Connect:** The client initiates a WebSocket connection to the endpoint using the `scan_id`.
2. **Listen:** The server will push JSON payloads containing progress updates and newly found vulnerabilities.
3. **Keep-Alive (Optional):** The connection remains open until the scan finishes. You can safely send keep-alive text messages if your client requires it, but it is not strictly necessary. 
4. **Close:** The server will automatically close the stream (or you can disconnect) when the scan completes or if a timeout/error occurs.

## Message Payloads

All messages sent from the server to the client are formatted as JSON objects with a `type` property indicating the nature of the message.

### 1. Progress Update (`"type": "progress"`)

Sent periodically (every ~5 seconds) while the scan is running. This payload includes the current completion percentage, any new alerts discovered since the last poll, and the total number of alerts found so far.

```json
{
  "type": "progress",
  "progress": 45,
  "new_alerts": [
    {
      "id": "123",
      "name": "Cross Site Scripting (Reflected)",
      "risk": "High",
      "url": "http://example.com/search?q=..."
    }
  ],
  "total_alerts": 5
}
```

**Fields:**
- `type` (string): Always `"progress"`.
- `progress` (integer): The scan completion percentage (0 - 99).
- `new_alerts` (list of objects): Vulnerabilities discovered during the last polling interval.
  - `id` (string): The unique ZAP identifier for the alert.
  - `name` (string): The title/name of the vulnerability.
  - `risk` (string): The risk level (e.g., "High", "Medium", "Low", "Informational").
  - `url` (string): The URL where the vulnerability was detected.
- `total_alerts` (integer): The total number of unique vulnerabilities found so far.

### 2. Scan Completed (`"type": "done"`)

Sent exactly once when the scan reaches 100% completion.

```json
{
  "type": "done",
  "progress": 100,
  "alerts_count": 12,
  "total_alerts": 12
}
```

**Fields:**
- `type` (string): Always `"done"`.
- `progress` (integer): Always `100`.
- `alerts_count` (integer): The raw number of alerts ultimately saved to the database.
- `total_alerts` (integer): The total number of alerts tracked during the dynamic stream.

### 3. Error (`"type": "error"`)

Sent if the scan fails, times out, or encounters an internal backend exception.

```json
{
  "type": "error",
  "message": "Scan timeout"
}
```

**Fields:**
- `type` (string): Always `"error"`.
- `message` (string): A description of the error that occurred.

## Client JavaScript Example

```javascript
// Example using the native browser WebSocket API

const scanId = "123e4567-e89b-12d3-a456-426614174000";
const ws = new WebSocket(`ws://localhost:8000/api/v1/zap/ws/scan/${scanId}`);

ws.onopen = () => {
    console.log("Connected to scan monitor.");
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
        case "progress":
            console.log(`Scan Progress: ${data.progress}%`);
            console.log(`Total vulnerabilities found: ${data.total_alerts}`);
            
            if (data.new_alerts && data.new_alerts.length > 0) {
                data.new_alerts.forEach(alert => {
                    console.warn(`[NEW] ${alert.risk} Risk: ${alert.name} at ${alert.url}`);
                });
            }
            break;
            
        case "done":
            console.log("Scan completed successfully!");
            // Trigger UI to fetch full report or redirect user
            ws.close();
            break;
            
        case "error":
            console.error("Scan error:", data.message);
            ws.close();
            break;
            
        default:
            console.log("Unknown message type:", data);
    }
};

ws.onclose = () => {
    console.log("Disconnected from scan monitor.");
};
```
