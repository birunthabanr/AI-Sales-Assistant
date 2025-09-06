import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User, Sparkles } from "lucide-react";
import Navigation from "@/components/Navigation";
import supabase from "../config/supabaseClient";
import AnimatedBackground from "@/components/AnimationBackground";

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
      const response = await fetch("http://localhost:3000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: userMessage }),
      });

      if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("Backend error:", errorData);
      return errorData.error || `HTTP error: ${response.status}`;
      }

      const data = await response.json();
      console.log("Backend response:", data);


      if (data && data.action === "chat") return data.result;
      if (data && typeof data.result === "object") return JSON.stringify(data.result, null, 2);
      if (data && data.result) return String(data.result);

      // fallback if backend only sends error
      return data?.error || "Unexpected response from server";
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
    
    const lastMessage = document.querySelector(".chat-message:last-child");
    lastMessage?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 to-violet-950 text-gray-100">
      <AnimatedBackground/>
      <Navigation />
      <div className="max-w-4xl mx-auto p-4">
        <Card className="h-[calc(95vh-8rem)] bg-gray-900/40 backdrop-blur-xl border border-indigo-500/30 shadow-2xl shadow-purple-500/10 rounded-2xl overflow-hidden">
          <CardHeader className="bg-gradient-to-r from-indigo-600 to-violet-600 border-b border-indigo-400/30">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-white/10 rounded-full backdrop-blur-sm">
                <Sparkles className="h-6 w-6 text-amber-300" />
              </div>
              <CardTitle className="text-xl font-bold text-white">
                AI Assistant
              </CardTitle>
            </div>
            <p className="text-sm text-indigo-100/80 mt-1">
              Ask me anything, I'm here to help!
            </p>
          </CardHeader>
          <CardContent className="flex flex-col h-full p-0">
            <ScrollArea className="flex-1 p-6 custom-scrollbar pb-28">
              <div className="space-y-6">
                {messages.length === 0 && (
                  <div className="text-center py-12">
                    <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 mb-6">
                      <Bot className="h-12 w-12 text-purple-400" />
                    </div>
                    <h3 className="text-xl font-medium text-gray-200 mb-2">
                      Start a conversation
                    </h3>
                    <p className="text-gray-400 max-w-md mx-auto">
                      Ask me anything and I'll do my best to assist you with helpful information and resources.
                    </p>
                  </div>
                )}
                
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex items-start space-x-3 ${
                      message.sender === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    {message.sender !== "user" && (
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg border-2 border-blue-400/30">
                        <Bot className="h-5 w-5 text-white" />
                      </div>
                    )}
                    <div
                      className={`relative max-w-[75%] rounded-2xl px-4 py-3 shadow-lg transition-all duration-300 transform origin-bottom ${
                        message.sender === "user"
                          ? "bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-br-md"
                          : "bg-gradient-to-r from-slate-800 to-gray-800 text-white rounded-bl-md border border-gray-700"
                      } animate-in fade-in-0 slide-in-from-bottom-3`}
                    >
                      <p className="whitespace-pre-wrap leading-relaxed">
                        {message.text}
                      </p>
                      <p className="text-xs opacity-70 mt-2 text-right">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                      
                      {/* Message corner accent */}
                      <div className={`absolute w-3 h-3 -bottom-3 ${
                        message.sender === "user" 
                          ? "right-0 bg-fuchsia-600" 
                          : "left-0 bg-gray-800"
                      }`} style={{clipPath: "polygon(0 0, 100% 0, 100% 100%)"}} />
                    </div>
                    {message.sender === "user" && (
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center shadow-lg border-2 border-fuchsia-400/30">
                        <User className="h-5 w-5 text-white" />
                      </div>
                    )}
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex items-start space-x-3 animate-pulse">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg">
                      <Bot className="h-5 w-5 text-white" />
                    </div>
                    <div className="max-w-[50%] rounded-2xl px-4 py-3 bg-gray-800 shadow-md">
                      <div className="flex items-center space-x-1.5">
                        <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Input Section */}
          </CardContent>
        </Card>
        <div className="border-t border-gray-700/50 p-4 rounded-3xl bg-gradient-to-r from-gray-900/70 to-gray-800/70 backdrop-blur-md">
          <div className="flex items-center space-x-3">
            <Input
              placeholder="Type your message..."
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="flex-1 bg-gray-800/60 border-gray-600/50 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-purple-500/30 rounded-xl py-5"
            />
            <Button
              onClick={sendMessage}
              disabled={isLoading || !newMessage.trim()}
              className="shrink-0 bg-gradient-to-r from-violet-600 to-fuchsia-600 hover:from-violet-500 hover:to-fuchsia-500 text-white rounded-xl shadow-lg h-11 w-11 p-0 transition-all duration-300 hover:scale-105"
            >
              <Send className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;