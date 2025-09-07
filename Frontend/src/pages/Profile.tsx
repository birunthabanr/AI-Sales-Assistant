import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import Navigation from "@/components/Navigation";
import { useEffect, useState } from "react";
import supabase from "../config/supabaseClient";
import AnimatedBackground from "@/components/AnimationBackground";

const Profile = () => {
  const [User, setUser] = useState<any>(null);

  useEffect(() => {
    const details_from_supabase = async () => {
      const Client_ID = localStorage.getItem("client_id");
      if (!Client_ID) return;

      const { data, error } = await supabase
        .from("client")
        .select("*")
        .eq("client_id", Client_ID)
        .single();

      if (error) {
        console.error("Error fetching client:", error);
      } else {
        setUser(data);
      }
    };

    details_from_supabase();
  }, []);

  if (!User) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-100">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-muted-foreground text-indigo-700">Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 to-violet-950 text-gray-100">
      <AnimatedBackground/>
      <Navigation />
      <div className="max-w-4xl mx-auto p-6">
        <Card className="shadow-2xl border-0 rounded-3xl overflow-hidden bg-gradient-to-br from-white to-indigo-50/50 backdrop-blur-sm animate-fade-in">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500"></div>
          <CardHeader className="border-b border-indigo-100/50 pb-5">
            <CardTitle className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              User Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {/* Profile header */}
            <div className="flex flex-col md:flex-row items-center space-y-6 md:space-y-0 md:space-x-8 mb-8 animate-slide-up">
              <div className="relative">
                <Avatar className="h-24 w-24 ring-4 ring-white/80 shadow-xl">
                  <AvatarImage src="" />
                  <AvatarFallback className="text-xl font-semibold bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
                    {User.client_name
                      .split(" ")
                      .map((n: string) => n[0])
                      .join("")}
                  </AvatarFallback>
                </Avatar>
                <div className="absolute -bottom-2 -right-2 w-6 h-6 rounded-full bg-green-500 border-2 border-white"></div>
              </div>
              <div className="text-center md:text-left">
                <h2 className="text-2xl font-bold text-gray-900 mb-1">{User.client_name}</h2>
                <p className="text-gray-500 text-sm mb-2 font-mono">ID: {User.client_id.slice(0, 8)}...</p>
                <div className="inline-flex items-center px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 text-xs font-medium">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                  </svg>
                  Joined: {new Date(User.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8 animate-slide-up" style={{ animationDelay: "0.1s" }}>
              <div className="flex items-center justify-between p-5 rounded-2xl bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg transition-all hover:scale-[1.02]">
                <div className="flex items-center">
                  <div className="p-2 bg-white/20 rounded-lg mr-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <span className="font-medium">Chats</span>
                </div>
                <Badge className="bg-white text-indigo-600 text-lg px-3 py-1 rounded-full shadow-md">
                  {User.client_chat?.length || 0}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-5 rounded-2xl bg-gradient-to-r from-gray-700 to-gray-800 text-white shadow-lg transition-all hover:scale-[1.02]">
                <div className="flex items-center">
                  <div className="p-2 bg-white/20 rounded-lg mr-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                  <span className="font-medium">Company</span>
                </div>
                <Badge variant="outline" className="bg-white/10 text-white border-white/30 text-lg px-3 py-1 rounded-full">
                  {User.company_id || "No company"}
                </Badge>
              </div>
            </div>

            {/* Chat history */}
            <div className="border-t border-gray-200/70 pt-6 animate-slide-up" style={{ animationDelay: "0.2s" }}>
              <div className="flex items-center justify-between mb-5">
                <h3 className="font-semibold text-lg text-gray-900 flex items-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-indigo-500" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                  </svg>
                  Recent Chats
                </h3>
                <span className="text-xs text-gray-500">{User.client_chat?.length || 0} messages</span>
              </div>
              <div className="space-y-4 max-h-72 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-indigo-300 scrollbar-track-transparent scrollbar-thumb-rounded-full">
                {User.client_chat?.map((msg: any, index: number) => (
                  <div
                    key={msg.id}
                    className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"} animate-fade-in`}
                    style={{ animationDelay: `${index * 0.05}s` }}
                  >
                    <div
                      className={`px-4 py-3 rounded-2xl shadow-sm max-w-xs transition-all duration-300 hover:scale-[1.02] ${
                        msg.sender === "user"
                          ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-br-none"
                          : "bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800 rounded-bl-none"
                      }`}
                    >
                      <div className="text-sm">{msg.text}</div>
                      <div className={`text-xs mt-2 opacity-80 text-right ${msg.sender === "user" ? "text-indigo-100" : "text-gray-500"}`}>
                        {new Date(msg.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <style>{`
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slide-up {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
        .animate-fade-in {
          animation: fade-in 0.6s ease-out forwards;
        }
        .animate-slide-up {
          animation: slide-up 0.6s ease-out forwards;
        }
        .scrollbar-thin::-webkit-scrollbar {
          width: 4px;
        }
        .scrollbar-thumb-rounded-full::-webkit-scrollbar-thumb {
          border-radius: 10px;
        }
      `}</style>
    </div>
  );
};

export default Profile;