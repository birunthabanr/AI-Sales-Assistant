import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send } from "lucide-react";
import Navigation from "@/components/Navigation";
import React, { useEffect } from 'react';
import supabase from "../config/supabaseClient.js"



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

  useEffect(() => {
    const fetchChat = async () => {
      const clientId = "f9035a5d-b169-4de0-8ed6-b4cfd77d1484";

      const { data, error } = await supabase
        .from("client")
        .select("client_chat")
        .eq("client_id", clientId)
        .single();

      if (error) {
        console.error("Error fetching chat:", error);
        return;
      }

      if (data && data.client_chat) {
        const chatWithDate = data.client_chat.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
        setMessages(chatWithDate);
      }
    };

    fetchChat();
  }, []);

  const sendMessageToBackend = async (userMessage: string): Promise<string> => {
    console.log("sending..")
   try {
    console.log("Sending payload:", JSON.stringify({ prompt: userMessage }));
    const response = await fetch("http://localhost:5000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt: userMessage, // backend expects "prompt"
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // backend returns { action, result }
    if (data.action === "chat") {
      return data.result; // plain LLM reply
    } else if (typeof data.result === "object") {
      // pretty-print structured data like customers or bookings
      return JSON.stringify(data.result, null, 2);
    } else {
      return String(data.result);
    }
  } catch (error) {
    console.error("Error sending message to backend:", error);
    return "Sorry, I'm having trouble connecting to the server. Please try again later.";
    }
  };



  const updateSupabaseChat = async (updatedMessages: Message[]) => {
    try {
      const clientId = "f9035a5d-b169-4de0-8ed6-b4cfd77d1484";
      
      const { error } = await supabase
        .from("client")
        .update({ 
          client_chat: updatedMessages.map(msg => ({
            id: msg.id,
            text: msg.text,
            sender: msg.sender,
            timestamp: msg.timestamp.toISOString()
          }))
        })
        .eq("client_id", clientId);

      if (error) {
        console.error('Error updating Supabase:', error);
      }
    } catch (error) {
      console.error('Error in updateSupabaseChat:', error);
    }
  };

  const sendMessage = async () => {
    if (newMessage.trim() && !isLoading) {
      const userMessage: Message = {
        id: Date.now(),
        text: newMessage,
        sender: "user",
        timestamp: new Date(),
      };
      
      // Add user message immediately
      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      setNewMessage("");
      setIsLoading(true);
      console.log(newMessage)
      try {
        // Send to backend and get response
        const botResponse = await sendMessageToBackend(newMessage);
        
        const botMessage: Message = {
          id: Date.now() + 1,
          text: botResponse,
          sender: "bot",
          timestamp: new Date(),
        };
        
        // Add bot message and update state
        const finalMessages = [...updatedMessages, botMessage];
        setMessages(finalMessages);
        
        // Update Supabase with the complete conversation
        await updateSupabaseChat(finalMessages);
        
      } catch (error) {
        console.error('Error in sendMessage:', error);
        const errorMessage: Message = {
          id: Date.now() + 1,
          text: "Sorry, something went wrong. Please try again.",
          sender: "bot",
          timestamp: new Date(),
        };
        const finalMessages = [...updatedMessages, errorMessage];
        setMessages(finalMessages);
        await updateSupabaseChat(finalMessages);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) {
      sendMessage();
    }
  };

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    const scrollArea = document.querySelector('[data-radix-scroll-area-viewport]');
    if (scrollArea) {
      scrollArea.scrollTop = scrollArea.scrollHeight;
    }
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
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
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