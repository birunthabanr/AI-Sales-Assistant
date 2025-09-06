import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send } from "lucide-react";
import Navigation from "@/components/Navigation";
import supabase from "../config/supabaseClient";

interface Message {
  id: number;
  text: string;
  sender: "user" | "bot";
  timestamp: Date;
}

const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [clientId, setClientId] = useState<string | null>(null);

  useEffect(() => {
    const storedId = localStorage.getItem("client_id");
    if (storedId) {
      setClientId(storedId);
    }
  }, []);

  useEffect(() => {
    if (!clientId) return;

    const fetchChat = async () => {
      const { data, error } = await supabase
        .from("client")
        .select("client_chat")
        .eq("client_id", clientId)
        .single();

      if (error) {
        console.error("Error fetching chat:", error);
        return;
      }

      if (data?.client_chat) {
        const chatWithDate = data.client_chat.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
        setMessages(chatWithDate);
      }
    };

    fetchChat();
  }, [clientId]);

  const sendMessageToBackend = async (userMessage: string): Promise<string> => {
    try {
      const response = await fetch("http://localhost:5000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: userMessage }),
      });

      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
      const data = await response.json();

      if (data.action === "chat") return data.result;
      if (typeof data.result === "object") return JSON.stringify(data.result, null, 2);
      return String(data.result);
    } catch (error) {
      console.error("Error sending message to backend:", error);
      return "Sorry, I'm having trouble connecting to the server. Please try again later.";
    }
  };

  const updateSupabaseChat = async (updatedMessages: Message[]) => {
    if (!clientId) return;
    const { error } = await supabase
      .from("client")
      .update({
        client_chat: updatedMessages.map(msg => ({
          id: msg.id,
          text: msg.text,
          sender: msg.sender,
          timestamp: msg.timestamp.toISOString(),
        })),
      })
      .eq("client_id", clientId);

    if (error) console.error("Error updating Supabase:", error);
  };

  const sendMessage = async () => {
    if (newMessage.trim() && !isLoading) {
      const userMessage: Message = {
        id: Date.now(),
        text: newMessage,
        sender: "user",
        timestamp: new Date(),
      };

      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      setNewMessage("");
      setIsLoading(true);

      try {
        const botResponse = await sendMessageToBackend(newMessage);

        const botMessage: Message = {
          id: Date.now() + 1,
          text: botResponse,
          sender: "bot",
          timestamp: new Date(),
        };

        const finalMessages = [...updatedMessages, botMessage];
        setMessages(finalMessages);
        await updateSupabaseChat(finalMessages);
      } catch (error) {
        console.error("Error in sendMessage:", error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) sendMessage();
  };

  // Auto-scroll
  useEffect(() => {
    const scrollArea = document.querySelector('[data-radix-scroll-area-viewport]');
    if (scrollArea) scrollArea.scrollTop = scrollArea.scrollHeight;
  }, [messages]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950 text-gray-100">
  <Navigation />
  <div className="max-w-4xl mx-auto p-4">
    <Card className="h-[calc(95vh-8rem)] bg-gray-900/70 backdrop-blur-xl border border-gray-800 shadow-2xl rounded-2xl">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-white">
          💬 Chat with AI
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col h-full">
        <ScrollArea className="flex-1 mb-4 pr-4 custom-scrollbar">
          <div className="space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex items-end space-x-2 ${
                  message.sender === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {message.sender !== "user" && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs shadow-md">
                    🤖
                  </div>

                )}
                <div
                  className={`relative max-w-[70%] rounded-2xl px-4 py-3 shadow-lg transition ${
                    message.sender === "user"
                      ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                      : "bg-gradient-to-r from-cyan-600 to-blue-600 text-white"
                  } animate-fadeIn`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {message.text}
                  </p>
                  <p className="text-[10px] opacity-70 mt-1 text-right">
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
                {message.sender === "user" && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white text-xs shadow-md">
                    👤
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center text-white text-xs shadow-md">
                  🤖
                </div>
                <div className="max-w-[70%] rounded-2xl px-4 py-3 bg-gray-800 shadow-md">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Input Section */}
        <div className="flex items-center space-x-2 p-2 bg-gray-800 rounded-xl shadow-md">
          <Button
            variant="ghost"
            size="icon"
            className="text-gray-400 hover:text-white"
          >
            😊
          </Button>
          <Input
            placeholder="Type your message..."
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            className="flex-1 bg-transparent border-0 text-gray-100 placeholder-gray-400 focus:ring-0"
          />
          <Button
            onClick={sendMessage}
            disabled={isLoading || !newMessage.trim()}
            className="shrink-0 bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 text-white rounded-xl shadow-md"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
</div>

  );
};

export default Chat;
