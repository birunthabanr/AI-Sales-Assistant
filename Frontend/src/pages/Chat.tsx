import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User, Sparkles } from "lucide-react";
import Navigation from "@/components/Navigation";
import supabase from "../config/supabaseClient";
import AnimatedBackground from "@/components/AnimationBackground";
import Sidebar from "@/components/leftchatbar";

interface Message {
  id: number;
  text: string;
  sender: "user" | "bot";
  timestamp: Date;
}

interface ChatTab {
  id: number;
  tab: string;
  content: Message[];
}

const Chat = () => {
  const [chatTabs, setChatTabs] = useState<ChatTab[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeChatId, setActiveChatId] = useState<number | null>(null);
  const [newMessage, setNewMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [userid, setuserid] = useState<string | null>(null);

  // ✅ Load client_id from localStorage
  useEffect(() => {
    const storedId = localStorage.getItem("user_id");
    console.log(storedId)
    if (storedId) setuserid(storedId);
  }, []);

  // ✅ Fetch chats from Supabase
  useEffect(() => {
  if (!userid) return;

  const fetchChats = async () => {
    const { data, error } = await supabase
      .from("users")
      .select("chat_logs")
      .eq("id", userid)
      .single(); // ✅ ensure only one row is returned

    if (error) {
      console.error("Error fetching chats:", error);
      return;
    }

    if (data?.chat_logs) {
      const formatted = data.chat_logs.map((chat: ChatTab) => ({
        ...chat,
        content: chat.content.map((msg: Message) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        })),
      }));

      setChatTabs(formatted);
      localStorage.setItem("chats", JSON.stringify(formatted));
    }
  };

  fetchChats();
}, [userid]);


  // ✅ Auto-scroll
  useEffect(() => {
    const scrollArea = document.querySelector(
      '[data-radix-scroll-area-viewport]'
    );
    if (scrollArea) scrollArea.scrollTop = scrollArea.scrollHeight;
  }, [messages]);

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


      if (data.action === "chat") return data.result;
      if (typeof data.result === "object")
        return JSON.stringify(data.result, null, 2);
      return String(data.result);
    } catch (error) {
      console.error("Error sending message to backend:", error);
      return "⚠️ Sorry, I'm having trouble connecting to the server.";
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !activeChatId) return;

    const userMessage: Message = {
      id: Date.now(),
      text: newMessage,
      sender: "user",
      timestamp: new Date(),
    };

    const updated = [...messages, userMessage];
    setMessages(updated);
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

      const finalMessages = [...updated, botMessage];
      setMessages(finalMessages);

      // ✅ Update Supabase
      const { error } = await supabase
        .from("chat_log")
        .update({
          content: finalMessages.map((m) => ({
            ...m,
            timestamp: m.timestamp.toISOString(),
          })),
        })
        .eq("id", activeChatId);

      if (error) console.error("Error updating Supabase:", error);

      // ✅ Update local state + localStorage
      const newTabs = chatTabs.map((tab) =>
        tab.id === activeChatId ? { ...tab, content: finalMessages } : tab
      );
      setChatTabs(newTabs);
      localStorage.setItem("chats", JSON.stringify(newTabs));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isLoading) sendMessage();
  };

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 to-violet-950 text-gray-100">
      <AnimatedBackground />
      <Navigation />

      <div className="flex flex-1">
        <Sidebar
          chats={chatTabs}
          activeChatId={activeChatId}
          send_id_to_chat={(id) => {
            setActiveChatId(id);
            const selected = chatTabs.find((c) => c.id === id);
            setMessages(selected ? selected.content : []);
          }}
        />

        {/* Chat Area */}
        <div className="max-w-4xl mx-auto p-4 flex-1 flex flex-col">
          <Card className="h-[calc(95vh-8rem)] bg-gray-900/40 backdrop-blur-xl border border-indigo-500/30 shadow-2xl shadow-purple-500/10 rounded-2xl overflow-hidden flex flex-col">
            <CardHeader className="bg-gradient-to-r from-indigo-600 to-violet-600 border-b border-indigo-400/30">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-white/10 rounded-full">
                  <Sparkles className="h-6 w-6 text-amber-300" />
                </div>
                <CardTitle className="text-xl font-bold text-white">
                  AI Assistant
                </CardTitle>
              </div>
              <p className="text-sm text-indigo-100/80 mt-1">
                Ask me anything, I&apos;m here to help!
              </p>
            </CardHeader>

            <CardContent className="flex flex-col h-full p-0">
              <ScrollArea className="flex-1 p-6 custom-scrollbar">
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
                        Ask me anything and I&apos;ll do my best to assist you.
                      </p>
                    </div>
                  )}

                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex items-start space-x-3 ${
                        message.sender === "user"
                          ? "justify-end"
                          : "justify-start"
                      }`}
                    >
                      {message.sender !== "user" && (
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                          <Bot className="h-5 w-5 text-white" />
                        </div>
                      )}
                      <div
                        className={`relative max-w-[75%] rounded-2xl px-4 py-3 ${
                          message.sender === "user"
                            ? "bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white"
                            : "bg-gradient-to-r from-slate-800 to-gray-800 text-white border border-gray-700"
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{message.text}</p>
                        <p className="text-xs opacity-70 mt-2 text-right">
                          {message.timestamp.toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </p>
                      </div>
                      {message.sender === "user" && (
                        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center">
                          <User className="h-5 w-5 text-white" />
                        </div>
                      )}
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex items-start space-x-3 animate-pulse">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
                        <Bot className="h-5 w-5 text-white" />
                      </div>
                      <div className="max-w-[50%] rounded-2xl px-4 py-3 bg-gray-800">
                        <div className="flex space-x-1.5">
                          <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" />
                          <div
                            className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"
                            style={{ animationDelay: "150ms" }}
                          />
                          <div
                            className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"
                            style={{ animationDelay: "300ms" }}
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Input */}
          <div className="border-t border-gray-700/50 p-4 bg-gradient-to-r from-gray-900/70 to-gray-800/70">
            <div className="flex items-center space-x-3">
              <Input
                placeholder="Type your message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !isLoading) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                disabled={isLoading}
                className="flex-1 bg-gray-800/60 border-gray-600/50 text-gray-100 rounded-xl py-5"
              />
              <Button
                onClick={sendMessage}
                disabled={isLoading || !newMessage.trim()}
                className="shrink-0 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl h-11 w-11"
              >
                <Send className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
