import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import Navigation from "@/components/Navigation";
import { useEffect, useState } from "react";
import supabase from "../config/supabaseClient";

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
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-muted-foreground">Loading profile...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-white to-gray-50">
      <Navigation />
      <div className="max-w-7xl mx-auto p-6">
        <Card className="shadow-xl border-none rounded-2xl">
          <CardHeader className="border-b border-gray-200">
            <CardTitle className="text-2xl font-semibold text-gray-900">
              User Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            {/* Profile header */}
            <div className="flex items-center space-x-6 mb-6">
              <Avatar className="h-20 w-20 ring-2 ring-indigo-500 ring-offset-2">
                <AvatarImage src="" />
                <AvatarFallback className="text-xl text-gray-700">
                  {User.client_name
                    .split(" ")
                    .map((n: string) => n[0])
                    .join("")}
                </AvatarFallback>
              </Avatar>
              <div>
                <h2 className="text-xl font-bold text-gray-900">{User.client_name}</h2>
                <p className="text-gray-500">ID: {User.client_id}...</p>
                <p className="text-sm text-gray-400">
                  Joined: {new Date(User.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
              <div className="flex items-center justify-between p-4 rounded-xl bg-indigo-50 shadow-sm">
                <span className="text-gray-700">Chats</span>
                <Badge variant="secondary">{User.client_chat?.length || 0}</Badge>
              </div>
              <div className="flex items-center justify-between p-4 rounded-xl bg-gray-100 shadow-sm">
                <span className="text-gray-700">Company</span>
                <Badge variant="outline">
                  {User.company_id || "No company"}
                </Badge>
              </div>
            </div>

            {/* Chat history */}
            <div className="border-t border-gray-200 pt-4">
              <h3 className="font-medium mb-3 text-gray-800">Recent Chats</h3>
              <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                {User.client_chat.map((msg: any) => (
                  <div
                    key={msg.id}
                    className={`flex ${
                      msg.sender === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`px-4 py-2 rounded-xl text-sm shadow-sm max-w-xs ${
                        msg.sender === "user"
                          ? "bg-indigo-500 text-white rounded-br-none"
                          : "bg-gray-200 text-gray-800 rounded-bl-none"
                      }`}
                    >
                      {msg.text}
                      <div className="text-[10px] mt-1 opacity-70 text-right">
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
    </div>
  );
};

export default Profile;
