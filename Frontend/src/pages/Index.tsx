import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import supabase from "../config/supabaseClient";
import { useAuthListener } from "./useAuth";
import AnimatedBackground from "@/components/AnimationBackground";

const Index = () => {
  const navigate = useNavigate();
  const { session } = useAuthListener();

  // ✅ Google OAuth Login
  const handleGoogleLogin = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
    });
    if (error) console.error("Google login error:", error);
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <AnimatedBackground />
      <div className="from-indigo-600 to-violet-600 backdrop-blur-md shadow-xl rounded-2xl p-10 max-w-md w-full text-center space-y-6">
        <h1 className="text-4xl font-extrabold text-gray-900">
          Welcome to <span className="text-indigo-600">ChatApp</span>
        </h1>
        <p className="text-lg text-gray-600">
          Chat, schedule events, and manage your profile all in one place!
        </p>

        <div className="pt-4">
          {session ? (
            <Button
              className="w-full rounded-xl bg-green-600 hover:bg-green-700 text-white text-lg py-6"
              onClick={() => navigate("/chat")}
            >
              Go to Chat
            </Button>
          ) : (
            <Button
              className="w-full rounded-xl bg-red-600 hover:bg-red-700 text-white text-lg py-6"
              onClick={handleGoogleLogin}
            >
              Continue with Google
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Index;
