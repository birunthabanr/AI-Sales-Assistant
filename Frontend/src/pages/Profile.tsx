import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import Navigation from "@/components/Navigation";
import { useEffect, useState } from "react";
import supabase from "../config/supabaseClient";
import AnimatedBackground from "@/components/AnimationBackground";

const Profile = () => {
  const [User, setUser] = useState<any>(null);
  const [newName, setNewName] = useState("");
  const [loading, setLoading] = useState(false);
  const [cleanConfirm, setCleanConfirm] = useState(false);

  useEffect(() => {
    const fetchUser = async () => {
      const userId = localStorage.getItem("user_id");
      if (!userId) return;

      const { data, error } = await supabase
        .from("users")
        .select("*")
        .eq("id", userId)
        .single();

      if (error) console.error("Error fetching user:", error);
      else setUser(data);
    };

    fetchUser();
  }, []);

  const handleNameChange = async () => {
    if (!newName.trim()) return alert("Enter a valid name");

    setLoading(true);

    const { error } = await supabase
      .from("users")
      .update({ name: newName })
      .eq("id", User.id);

    if (error) alert("Failed to update name");
    else {
      alert("Name updated successfully!");
      setUser({ ...User, name: newName });
      setNewName("");
    }

    setLoading(false);
  };

  const handleCleanChats = async () => {
    if (!cleanConfirm) {
      setCleanConfirm(true);
      alert("Click 'Clean Chats' again to confirm deletion!");
      return;
    }

    setLoading(true);
    const { error } = await supabase
      .from("users")
      .update({ chat_logs: [] })
      .eq("id", User.id);

    if (error) alert("Failed to clean chats");
    else {
      alert("All chats deleted!");
      setUser({ ...User, chat_logs: [] });
    }
    setCleanConfirm(false);
    setLoading(false);
  };

  if (!User)
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-purple-100">
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-indigo-700 text-lg">Loading profile...</p>
        </div>
      </div>
    );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black text-gray-100">
      <AnimatedBackground />
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
                    {User.name
                      .split(" ")
                      .map((n: string) => n[0])
                      .join("")}
                  </AvatarFallback>
                </Avatar>
                <div className="absolute -bottom-2 -right-2 w-6 h-6 rounded-full bg-green-500 border-2 border-white"></div>
              </div>
              <div className="text-center md:text-left">
                <h2 className="text-2xl font-bold text-gray-900 mb-1">
                  {User.name}
                </h2>
                <p className="text-gray-500 text-sm mb-2 font-mono">
                  ID: {User.id.slice(0, 8)}...
                </p>
                <div className="inline-flex items-center px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 text-xs font-medium">
                  Joined: {new Date(User.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-8 animate-slide-up">
              <div className="flex items-center justify-between p-5 rounded-2xl bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg transition-all hover:scale-[1.02]">
                <span className="font-medium">Chats</span>
                <Badge className="bg-white text-indigo-600 text-lg px-3 py-1 rounded-full shadow-md">
                  {User.chat_logs?.length || 0}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-5 rounded-2xl bg-gradient-to-r from-gray-700 to-gray-800 text-white shadow-lg transition-all hover:scale-[1.02]">
                <span className="font-medium">Email</span>
                <Badge
                  variant="outline"
                  className="bg-white/10 text-white border-white/30 text-lg px-3 py-1 rounded-full"
                >
                  {User.email}
                </Badge>
              </div>
            </div>

            {/* Name Change */}
            <div className="mb-6 animate-slide-up">
              <h3 className="font-semibold text-lg text-gray-900 mb-3">
                Change Name
              </h3>
              <div className="flex flex-col md:flex-row items-center gap-3">
                <input
                  type="text"
                  placeholder="New Name"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="p-2 rounded-lg w-full md:w-1/3 text-black"
                />
                <button
                  onClick={handleNameChange}
                  disabled={loading}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700"
                >
                  {loading ? "Updating..." : "Update Name"}
                </button>
              </div>
            </div>

            {/* Clean Chats */}
            <div className="mb-6 animate-slide-up">
              <h3 className="font-semibold text-lg text-gray-900 mb-3">
                Manage Chats
              </h3>
              <button
                onClick={handleCleanChats}
                disabled={loading}
                className="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700"
              >
                {loading ? "Processing..." : "Clean Chats"}
              </button>
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
        .animate-fade-in { animation: fade-in 0.6s ease-out forwards; }
        .animate-slide-up { animation: slide-up 0.6s ease-out forwards; }
        .scrollbar-thin::-webkit-scrollbar { width: 4px; }
        .scrollbar-thumb-rounded-full::-webkit-scrollbar-thumb { border-radius: 10px; }
      `}</style>
    </div>
  );
};

export default Profile;
