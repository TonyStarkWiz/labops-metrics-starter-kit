#!/usr/bin/env python3
"""
Simple test webhook server for testing Teams Bot functionality
Run this to test your Teams Bot without needing a real Teams webhook
"""

import json
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Store received messages
received_messages = []

@app.route('/webhook', methods=['POST'])
def webhook():
    """Receive webhook messages"""
    try:
        data = request.get_json()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message_info = {
            "timestamp": timestamp,
            "content": data.get('text', ''),
            "title": data.get('title', ''),
            "sections": data.get('sections', []),
            "raw_data": data
        }
        
        received_messages.append(message_info)
        print(f"✅ Received message at {timestamp}")
        print(f"📝 Content: {data.get('text', '')[:100]}...")
        
        return jsonify({"status": "success", "message": "Message received"}), 200
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/messages', methods=['GET'])
def get_messages():
    """Get all received messages"""
    return jsonify({
        "total_messages": len(received_messages),
        "messages": received_messages
    })

@app.route('/clear', methods=['POST'])
def clear_messages():
    """Clear all received messages"""
    global received_messages
    received_messages.clear()
    return jsonify({"status": "success", "message": "Messages cleared"})

@app.route('/', methods=['GET'])
def home():
    """Home page with instructions"""
    return """
    <html>
    <head><title>Test Webhook Server</title></head>
    <body>
        <h1>🔗 Test Webhook Server for Teams Bot</h1>
        <p>This server simulates a Teams webhook for testing purposes.</p>
        
        <h2>📋 Webhook URL</h2>
        <p><strong>Use this URL in your Teams Bot:</strong></p>
        <code style="background: #f0f0f0; padding: 10px; display: block; margin: 10px 0;">
            http://localhost:5000/webhook
        </code>
        
        <h2>📊 Received Messages</h2>
        <p>Total messages: <strong>{}</strong></p>
        <p><a href="/messages">View all messages</a></p>
        
        <h2>🧹 Actions</h2>
        <form method="POST" action="/clear" style="margin: 10px 0;">
            <button type="submit">Clear All Messages</button>
        </form>
        
        <h2>📝 How to Test</h2>
        <ol>
            <li>Keep this server running</li>
            <li>In your Streamlit app, use: <code>http://localhost:5000/webhook</code></li>
            <li>Send a test message from the Teams Bot tab</li>
            <li>Check this page to see received messages</li>
        </ol>
        
        <h2>🔄 Status</h2>
        <p>Server is running and ready to receive webhooks!</p>
    </body>
    </html>
    """.format(len(received_messages))

if __name__ == '__main__':
    print("🚀 Starting Test Webhook Server...")
    print("📡 Webhook URL: http://localhost:5000/webhook")
    print("🌐 View messages: http://localhost:5000/messages")
    print("🏠 Home page: http://localhost:5000/")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

