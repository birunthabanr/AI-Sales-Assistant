import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { MessageCircle, Calendar, User, LogOut, Home } from "lucide-react";

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: "/chat", label: "Chat", icon: MessageCircle },
    { path: "/profile", label: "Profile", icon: User },
    { path: "/dashboard", label: "Dashboard", icon: Calendar },
  ];

  const handleLogout = () => {
    navigate("/");
  };

  return (
    <nav className="bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-500 border-b border-white/20 px-4 py-3 shadow-lg relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-4 -left-4 w-8 h-8 bg-yellow-400 rounded-full animate-pulse opacity-70"></div>
        <div className="absolute top-1/4 right-8 w-6 h-6 bg-pink-500 rounded-full animate-bounce opacity-60"></div>
        <div className="absolute bottom-2 left-1/4 w-4 h-4 bg-green-400 rounded-full animate-ping opacity-50"></div>
      </div>
      
      <div className="flex items-center justify-between max-w-6xl mx-auto relative z-10">
        {/* Left: Navigation Items */}
        <div className="flex items-center space-x-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Button
                key={item.path}
                onClick={() => navigate(item.path)}
                variant="ghost"
                className={`flex items-center space-x-2 px-4 py-2 rounded-xl transition-all duration-300 
                  ${isActive 
                    ? "bg-gradient-to-r from-yellow-400 to-orange-500 text-white shadow-lg transform scale-105" 
                    : "text-white/90 hover:text-white hover:bg-white/20 backdrop-blur-sm"
                  }`}
              >
                <Icon className="h-5 w-5" />
                <span className="text-sm font-semibold">{item.label}</span>
              </Button>
            );
          })}
        </div>

        {/* Right: Logout */}
        <Button
          variant="ghost"
          onClick={handleLogout}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-gradient-to-r from-pink-500 to-rose-600 text-white hover:from-pink-600 hover:to-rose-700 transform hover:scale-105 transition-all duration-300 shadow-md"
        >
          <LogOut className="h-5 w-5" />
          <span className="text-sm font-semibold">Logout</span>
        </Button>
      </div>
    </nav>
  );
};

export default Navigation;