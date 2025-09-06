import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { MessageCircle, Calendar, User, LogOut } from "lucide-react";

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: "/chat", label: "Chat", icon: MessageCircle },
    { path: "/calendar", label: "Calendar", icon: Calendar },
    { path: "/profile", label: "Profile", icon: User },
  ];

  const handleLogout = () => {
    navigate("/");
  };

  return (
    <nav className="bg-gradient-to-r from-gray-900 via-gray-800 to-gray-900 border-b border-gray-700 px-4 py-3 shadow-md">
      <div className="flex items-center justify-between max-w-6xl mx-auto">
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
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200 
                  ${isActive 
                    ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-md" 
                    : "text-gray-300 hover:text-white hover:bg-gray-700/50"
                  }`}
              >
                <Icon className="h-4 w-4" />
                <span className="text-sm font-medium">{item.label}</span>
              </Button>
            );
          })}
        </div>

        {/* Right: Logout */}
        <Button
          variant="ghost"
          onClick={handleLogout}
          className="flex items-center space-x-2 px-3 py-2 rounded-lg text-gray-300 hover:text-white hover:bg-red-600/80 transition-all duration-200"
        >
          <LogOut className="h-4 w-4" />
          <span className="text-sm font-medium">Logout</span>
        </Button>
      </div>
    </nav>

  );
};

export default Navigation;