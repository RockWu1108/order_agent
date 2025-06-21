import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Header from './components/Header';
import LoadingSpinner from './components/LoadingSpinner';
import FoodList from './components/FoodList';
import { FoodItem } from './types';
import ConfirmationMessage from './components/ConfirmationMessage';
import { getApiUrl } from './services/apiConfig'; // 導入 getApiUrl

// Main App Component
const App: React.FC = () => {
    // --- State Management ---
    const [threadId, setThreadId] = useState<string | null>(null);
    const [messages, setMessages] = useState<any[]>([]);
    const [input, setInput] = useState<string>('');
    const [isLoading, setIsLoading] = useState<boolean>(false);

    // State for structured data from the agent
    const [restaurants, setRestaurants] = useState<FoodItem[]>([]);
    const [formUrl, setFormUrl] = useState<string>('');

    const messagesEndRef = useRef<HTMLDivElement>(null);

    // --- Effects ---
    // Auto-scroll to the latest message
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Initialize threadId on first load
    useEffect(() => {
        setThreadId(uuidv4());
    }, []);

    // --- Core Logic ---
    const handleSend = async (messageContent?: string) => {
        const content = messageContent || input;
        if (!content.trim() || !threadId) return;

        setIsLoading(true);
        setRestaurants([]); // Clear previous results
        setFormUrl('');

        const userMessage = { role: 'user', content: content };
        setMessages(prev => [...prev, userMessage]);
        setInput('');

        try {
            const response = await fetch(getApiUrl('/api/chat'), { // 使用 getApiUrl 產生完整路徑
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: content, thread_id: threadId }),
            });

            if (!response.body) return;

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            // Process the stream from the backend
            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                     // Add a final confirmation message when the user confirms the restaurant
                    const lastUserMessage = messages[messages.length - 1];
                    if (lastUserMessage && lastUserMessage.role === 'user' && lastUserMessage.content.includes("我選")) {
                        const finalConfirmation = {
                            role: 'assistant',
                            content: '好的，我來為您處理後續的步驟！'
                        };
                        setMessages(prev => [...prev, finalConfirmation]);
                    }
                    break;
                };

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                lines.forEach(line => {
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonData = JSON.parse(line.substring(6));
                            handleStreamedData(jsonData);
                        } catch (error) {
                            console.error('Error parsing stream data:', error, 'Line:', line);
                        }
                    }
                });
            }
        } catch (error) {
            console.error('Failed to send message:', error);
            const errorMessage = { role: 'assistant', content: '抱歉，連線時發生錯誤。' };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    // Handles different types of data from the stream
    const handleStreamedData = (data: any) => {
        if (data.type === 'end') {
            setIsLoading(false);
            if (data.thread_id) {
                setThreadId(data.thread_id); // Ensure thread_id is persisted
            }
            return;
        }

        if (data.type === 'error') {
            const errorMessage = { role: 'assistant', content: `發生錯誤: ${data.content}` };
            setMessages(prev => [...prev, errorMessage]);
            return;
        }

        // --- Structured Data Handling ---
        if (data.type === 'restaurant_list') {
             // This is a custom event type we define for restaurant lists
            setRestaurants(data.data || []);
            const message = { role: 'assistant', content: "這是我為您找到的餐廳，請選擇一家：" };
            setMessages(prev => [...prev, message]);
            return;
        }

        if (data.type === 'form_created') {
             // This is a custom event type for when the form is ready
            setFormUrl(data.data.form_url);
            const message = { role: 'assistant', content: data.data.message };
            setMessages(prev => [...prev, message]);
            return;
        }

        // Default message handling
        if (data.content) {
            const message = { role: 'assistant', content: data.content };
             setMessages(prev => {
                // To avoid duplicate messages if the last one is the same
                if(prev.length > 0 && prev[prev.length - 1].content === message.content) {
                    return prev;
                }
                return [...prev, message]
            });
        }
    };

    // --- Render ---
    return (
        <div className="flex flex-col h-screen bg-gray-100 font-sans">
            <Header />
            <main className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((msg, index) => (
                    <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`rounded-lg px-4 py-2 max-w-lg ${msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-white text-gray-800'}`}>
                            {/* FIX: Add explicit types for map function parameters */}
                            {typeof msg.content === 'string' ? msg.content.split('\n').map((line: string, i: number) => <p key={i}>{line}</p>) : ''}
                        </div>
                    </div>
                ))}

                {isLoading && <LoadingSpinner />}

                {restaurants.length > 0 && (
                    <FoodList
                        items={restaurants}
                        onSelect={(restaurantName) => {
                           const selectionMessage = `我選這家: ${restaurantName}`;
                           setMessages(prev => [...prev, {role: 'user', content: selectionMessage}]);
                           handleSend(selectionMessage);
                           setRestaurants([]); // Hide list after selection
                        }}
                    />
                )}

                {formUrl && (
                     <ConfirmationMessage formUrl={formUrl} />
                )}

                <div ref={messagesEndRef} />
            </main>

            <footer className="bg-white border-t p-4">
                <div className="flex items-center">
                    <input
                        type="text"
                        className="flex-1 rounded-full border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="請輸入訊息..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        disabled={isLoading}
                    />
                    <button
                        className="ml-4 bg-blue-500 text-white rounded-full px-6 py-2 hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-400"
                        onClick={() => handleSend()}
                        disabled={isLoading}
                    >
                        傳送
                    </button>
                </div>
            </footer>
        </div>
    );
};

export default App;
