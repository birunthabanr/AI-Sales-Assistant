import { useState } from "react";
import { MessageSquare, Plus, ChevronLeft, ChevronRight } from "lucide-react";

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

type props = {
  send_id_to_chat: (id: number) => void; // function that takes an id
};

const Sidebar: React.FC<props> = ({ send_id_to_chat }) => {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  const openNewChat = () => {
    setActiveTab(0);
    send_id_to_chat(0); // ✅ also call parent if needed
  };

  const dummyPreviousMsg: ChatTab[] = [
    {
      id: 1,
      tab: "First Chat",
      content: [
        {
          id: 1,
          text: "Hello! Can you help me with my project?",
          sender: "user",
          timestamp: new Date("2025-09-11T15:05:00Z"),
        },
        {
          id: 2,
          text: "Of course 🚀 Tell me what you’re working on.",
          sender: "bot",
          timestamp: new Date("2025-09-11T15:05:05Z"),
        },
      ],
    },
    {
      id: 2,
      tab: "Second Chat",
      content: [
        {
          id: 3,
          text: "I’m building a chatbot with Supabase and Next.js.",
          sender: "user",
          timestamp: new Date("2025-09-11T15:06:00Z"),
        },
        {
          id: 4,
          text: "Nice choice! Supabase is great for storing chat history.",
          sender: "bot",
          timestamp: new Date("2025-09-11T15:06:12Z"),
        },
      ],
    },
    {
      id: 3,
      tab: "Third Chat",
      content: [
        {
          id: 5,
          text: "Yes, I’ll need Google login support later.",
          sender: "user",
          timestamp: new Date("2025-09-11T15:07:00Z"),
        },
        {
          id: 6,
          text: "Got it ✅ You can use Supabase Auth for that.",
          sender: "bot",
          timestamp: new Date("2025-09-11T15:07:15Z"),
        },
      ],
    },
  ];

  return (
    <div
      className={`${
        open ? "w-64" : "w-16"
      } h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-black text-gray-200 flex flex-col border-r border-gray-800 transition-all duration-300`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        {open && <h1 className="text-lg font-bold tracking-wide">Nexa - AI</h1>}
        <button
          onClick={() => setOpen(!open)}
          className="p-1.5 rounded-md hover:bg-gray-800 transition"
        >
          {open ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      {/* Primary Action */}
      <div className="px-2 py-3">
        <button
          className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-gray-800 transition"
          onClick={openNewChat}
        >
          <Plus size={20} />
          {open && <span>New Chat</span>}
        </button>
      </div>

      {/* Divider */}
      <hr className="border-gray-800 mx-2 my-2" />

      {/* Chat Tabs */}
      <div className="flex-1 overflow-y-auto px-2">
        {open && <p className="text-xs text-gray-500 mb-2">Recent Chats</p>}
        {dummyPreviousMsg.map((chat) => (
          <button
            key={chat.id}
            onClick={() => {
              setActiveTab(chat.id);
              send_id_to_chat(chat.id); // ✅ send id back to parent
            }}
            className={`flex items-center gap-4 w-full p-2 rounded-lg hover:bg-gray-800 transition ${
              activeTab === chat.id ? "bg-gray-800" : ""
            }`}
          >
            <MessageSquare size={18} />
            {open && <span className="truncate">{chat.tab}</span>}
          </button>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;
