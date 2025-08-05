import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send } from "lucide-react";
import Navigation from "@/components/Navigation";

interface Message {
  id: number;
  text: string;
  sender: "user" | "bot";
  timestamp: Date;
}

const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hello! How can I help you today?",
      sender: "bot",
      timestamp: new Date(Date.now() - 3600000),
    },
    {
      id: 2,
      text: "Hi there! I have a question about my account.",
      sender: "user",
      timestamp: new Date(Date.now() - 3500000),
    },
    {
      id: 3,
      text: "I'd be happy to help you with your account. What specific question do you have?",
      sender: "bot",
      timestamp: new Date(Date.now() - 3400000),
    },
  ]);
  const [newMessage, setNewMessage] = useState("");

  const sendMessage = () => {
    if (newMessage.trim()) {
      const userMessage: Message = {
        id: messages.length + 1,
        text: newMessage,
        sender: "user",
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, userMessage]);
      setNewMessage("");
      
      // Simulate bot response
      setTimeout(() => {
        const botMessage: Message = {
          id: messages.length + 2,
          text: "Thanks for your message! This is a dummy response. In a real implementation, this would connect to your backend API.",
          sender: "bot",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, botMessage]);
      }, 1000);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <div className="max-w-4xl mx-auto p-4">
        <Card className="h-[calc(100vh-8rem)]">
          <CardHeader>
            <CardTitle>Chat Support</CardTitle>
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
                      <p>{message.text}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
            <div className="flex space-x-2">
              <Input
                placeholder="Type your message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <Button onClick={sendMessage}>
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