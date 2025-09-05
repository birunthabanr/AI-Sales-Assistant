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
    <div className="min-h-screen bg-background">
      <Navigation />
      <div className="max-w-4xl mx-auto p-4">
        <Card className="h-[calc(100vh-8rem)]">
          <CardHeader>
            <CardTitle>Hello! How can I assist you today?</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col h-full">
            <ScrollArea className="flex-1 mb-4 pr-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-lg p-3 ${
                        message.sender === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted"
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.text}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="max-w-[70%] rounded-lg p-3 bg-muted">
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
            <div className="flex space-x-2">
              <Input
                placeholder="Type your message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                className="flex-1"
              />
              <Button
                onClick={sendMessage}
                disabled={isLoading || !newMessage.trim()}
                className="shrink-0"
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
