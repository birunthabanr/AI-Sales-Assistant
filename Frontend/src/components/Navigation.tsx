import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { MessageCircle, Calendar, User, LogOut } from "lucide-react";
import { useState, useEffect } from "react";
import supabase from "../config/supabaseClient";

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [privilege, setPrivilege] = useState(false);
  const [navItems, setNavItems] = useState([
    { path: "/chat", label: "Chat", icon: MessageCircle },
    { path: "/profile", label: "Profile", icon: User },
  ]);

  useEffect(() => {
    const fetchPrivilege = async () => {
      const id = localStorage.getItem("user_id");
      const { data, error } = await supabase
        .from("users")
        .select("is_admin")
        .eq("user_id", id)
        .single();

      if (error) {
        console.error(error);
        return;
      }

      const privilege = data.privilege; // normalize string

      if (privilege === true) {
        setPrivilege(true);
        setNavItems([
          { path: "/chat", label: "Chat", icon: MessageCircle },
          { path: "/profile", label: "Profile", icon: User },
          { path: "/dashboard", label: "Dashboard", icon: Calendar },
        ]);
      }
    };

    fetchPrivilege();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("user_id"); // clear session
    navigate("/");
  };

  return (
    <nav className="bg-gradient-to-r from-gray-950 via-gray-900 to-black border-b border-white/20 px-4 py-3 shadow-lg">
      <div className="flex items-center justify-between max-w-6xl mx-auto">
        <div className="flex items-center space-x-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Button
                key={item.path}
                onClick={() => navigate(item.path)}
                variant="ghost"
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-300 ${
                  isActive
                    ? "bg-gradient-to-r from-yellow-400 to-orange-500 text-white shadow-lg scale-105"
                    : "text-white/90 hover:text-white hover:bg-white/20 backdrop-blur-sm"
                }`}
              >
                <Icon className="h-5 w-5" />
                <span className="text-sm font-semibold">{item.label}</span>
              </Button>
            );
          })}
        </div>
        <Button
          variant="ghost"
          onClick={handleLogout}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-pink-500 to-rose-600 text-white hover:scale-105 transition-all duration-300 shadow-md"
        >
          <LogOut className="h-5 w-5" />
          <span className="text-sm font-semibold">Logout</span>
        </Button>
      </div>
    </nav>
  );
};

export default Navigation;
