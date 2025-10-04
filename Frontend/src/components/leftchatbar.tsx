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

type SidebarProps = {
  chats: ChatTab[];
  activeChatId: number | null;
  send_id_to_chat: (id: number) => void;
};

const Sidebar: React.FC<SidebarProps> = ({
  chats,
  activeChatId,
  send_id_to_chat,
}) => {
  const [open, setOpen] = useState(true);

  return (
    <div
      className={`${
        open ? "w-64" : "w-16"
      } h-<0.80> bg-gradient-to-b from-gray-950 via-gray-900 to-black text-gray-200 flex flex-col border-r border-gray-800 transition-all duration-300`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        {open && <h1 className="text-lg font-bold tracking-wide">Nexa - AI</h1>}
        <button
          onClick={() => setOpen(!open)}
          className="p-1.5 rounded-md hover:bg-gray-800"
          aria-label="Toggle sidebar"
        >
          {open ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>

      {/* New Chat */}
      <div className="px-2 py-3">
        <button
          className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-gray-800"
          onClick={() => send_id_to_chat(0)}
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
        {chats.map((chat) => (
          <button
            key={chat.id}
            onClick={() => send_id_to_chat(chat.id)}
            className={`flex items-center gap-4 w-full p-2 rounded-lg hover:bg-gray-800 ${
              activeChatId === chat.id ? "bg-gray-800" : ""
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
