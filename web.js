// web.js
const WebSocket = require('ws');
const zmq = require('zeromq');

// Create WebSocket server
const wss = new WebSocket.Server({ port: 8786 });
console.log('WebSocket server started on port 8786');

// Create ZMQ subscriber
async function run() {
    const sock = new zmq.Subscriber;
    await sock.connect("tcp://localhost:5555");
    await sock.subscribe("health_metrics");
    console.log('Connected to ZMQ publisher on port 5555');

    // Handle incoming ZMQ messages
    for await (const [topic, msg] of sock) {
        // Broadcast to all connected WebSocket clients
        wss.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                try {
                    client.send(msg.toString());
                } catch (error) {
                    console.error('Error sending to client:', error);
                }
            }
        });
    }
}

// Handle WebSocket connections
wss.on('connection', (ws) => {
    console.log('New client connected');

    ws.on('error', (error) => {
        console.error('WebSocket error:', error);
    });

    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

// Handle server errors
wss.on('error', (error) => {
    console.error('WebSocket server error:', error);
});

// Start ZMQ subscriber
run().catch(error => {
    console.error('ZMQ error:', error);
});

// Graceful shutdown
process.on('SIGINT', () => {
    wss.close(() => {
        console.log('WebSocket server closed');
        process.exit();
    });
});
