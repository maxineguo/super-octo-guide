import os
import requests
import json
from flask import Flask, request, jsonify, render_template_string

# -----------------------------------------------------------------------------
# FLASK APP SETUP
# -----------------------------------------------------------------------------
app = Flask(__name__)

# Load the API Key from Vercel's environment variables
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"

# -----------------------------------------------------------------------------
# HTML TEMPLATE (Frontend)
# -----------------------------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gemini Chat Interface</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');
        body {
            font-family: 'Inter', sans-serif;
            background-color: #f7f9fb;
        }
        #chat-container::-webkit-scrollbar {
            width: 8px;
        }
        #chat-container::-webkit-scrollbar-thumb {
            background-color: #cbd5e1;
            border-radius: 4px;
        }
        #chat-container::-webkit-scrollbar-track {
            background-color: #f1f5f9;
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">

    <div class="w-full max-w-2xl bg-white shadow-xl rounded-2xl overflow-hidden flex flex-col h-[80vh] md:h-[90vh]">
        
        <header class="p-4 bg-indigo-600 text-white shadow-md">
            <h1 class="text-xl font-bold">Gemini AI Chat</h1>
            <p class="text-sm opacity-80">Ask me anything!</p>
        </header>

        <main id="chat-container" class="flex-grow p-4 space-y-4 overflow-y-auto">
            <div class="flex justify-start">
                <div class="bg-blue-100 text-blue-800 p-3 rounded-xl rounded-tl-none max-w-[80%] shadow-sm">
                    Hello! I am a simple AI assistant. Type a question and press <strong>Enter</strong> or click <strong>Send</strong> to get a response.
                </div>
            </div>
        </main>

        <div class="p-4 border-t border-gray-200 bg-gray-50 flex items-end">
            <textarea
                id="user-input"
                class="flex-grow resize-none p-3 text-gray-700 border border-gray-300 rounded-xl focus:ring-indigo-500 focus:border-indigo-500 transition duration-150 overflow-hidden"
                placeholder="Type your message..."
                rows="1"
            ></textarea>

            <button
                id="send-button"
                class="ml-3 p-3 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-300 transition duration-150 transform hover:scale-105"
            >
                <svg id="send-icon" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                </svg>
                <svg id="loading-spinner" class="animate-spin h-6 w-6 text-white hidden" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            </button>
        </div>
    </div>

    <script>
        const userInput = document.getElementById('user-input');
        const chatContainer = document.getElementById('chat-container');
        const sendButton = document.getElementById('send-button');
        const sendIcon = document.getElementById('send-icon');
        const loadingSpinner = document.getElementById('loading-spinner');

        function autoExpand(field) {
            field.style.height = 'auto'; 
            field.style.overflowY = 'hidden';
            field.style.height = field.scrollHeight + 'px';
        }

        function addMessage(text, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('flex', isUser ? 'justify-end' : 'justify-start');
            
            const bubble = document.createElement('div');
            bubble.classList.add(
                'p-3',
                'rounded-xl',
                'max-w-[80%]',
                'shadow-md',
                isUser ? 'bg-indigo-600' : 'bg-white',
                isUser ? 'text-white' : 'text-gray-800',
                isUser ? 'rounded-br-none' : 'rounded-tl-none'
            );
            
            const formattedText = text
                .replace(/\\n/g, '<br>') 
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            
            bubble.innerHTML = formattedText;
            messageDiv.appendChild(bubble);
            chatContainer.appendChild(messageDiv);

            chatContainer.scrollTop = chatContainer.scrollHeight;
            return bubble;
        }
        
        function toggleLoading(isLoading) {
            sendButton.disabled = isLoading;
            userInput.disabled = isLoading;
            if (isLoading) {
                sendIcon.classList.add('hidden');
                loadingSpinner.classList.remove('hidden');
            } else {
                sendIcon.classList.remove('hidden');
                loadingSpinner.classList.add('hidden');
            }
        }

        async function sendMessage() {
            console.log("Attempting to send message...");
            
            const prompt = userInput.value.trim();
            if (!prompt) {
                console.log("Prompt is empty, aborting send.");
                return;
            }

            addMessage(prompt, true);
            
            userInput.value = '';
            userInput.style.height = 'auto'; 
            userInput.style.overflowY = 'hidden';
            
            toggleLoading(true);

            const aiBubble = addMessage('...', false);

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt: prompt }),
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error('API Error: ' + response.status + ' - ' + (error.error || 'Unknown error'));
                }

                const data = await response.json();
                const rawText = data.text;
                
                const finalFormattedText = rawText
                    .replace(/\\n/g, '<br>') 
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                    
                aiBubble.innerHTML = finalFormattedText;

            } catch (error) {
                console.error("Fetch error:", error);
                aiBubble.innerHTML = `<span class="text-red-600">Error: Could not connect to AI. Please check your browser console for details (F12) and ensure the <strong>GEMINI_API_KEY</strong> is correctly set in your Vercel environment.</span>`;
            } finally {
                toggleLoading(false);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }

        userInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        userInput.addEventListener('input', function() {
            autoExpand(this);
        });

        sendButton.addEventListener('click', sendMessage); 
        
        window.onload = () => {
             autoExpand(userInput);
        };

    </script>
</body>
</html>
"""

# -----------------------------------------------------------------------------
# FLASK ROUTES
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    """Serves the main chat application page."""
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/generate", methods=["POST"])
def generate_content():
    """Handles the request to the Gemini API."""
    if not GEMINI_API_KEY:
        app.logger.error("GEMINI_API_KEY environment variable not set.")
        return jsonify({"error": "Server configuration error: API Key missing. Please set the GEMINI_API_KEY environment variable."}), 500

    try:
        data = request.get_json()
        prompt = data.get("prompt")

        if not prompt:
            return jsonify({"error": "Prompt is missing."}), 400

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "tools": [{"google_search": {}}],
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", 
            headers=headers, 
            data=json.dumps(payload)
        )
        response.raise_for_status()

        result = response.json()
        
        generated_text = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No response generated.')

        return jsonify({"text": generated_text})

    except requests.exceptions.RequestException as e:
        app.logger.error(f"Gemini API request failed: {e}")
        return jsonify({"error": f"Failed to connect to AI service: {e}"}), 502
    except Exception as e:
        app.logger.error(f"An unexpected error occurred: {e}")
        return jsonify({"error": f"An unexpected server error occurred: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True)