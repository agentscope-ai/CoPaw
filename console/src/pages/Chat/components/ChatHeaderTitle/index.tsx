import React from "react";
import { useChatAnywhereSessionsState } from "@agentscope-ai/chat";
import { useIsMobile } from "../../../../hooks/useIsMobile";
import styles from "./index.module.less";

const ChatHeaderTitle: React.FC = () => {
  const { sessions, currentSessionId } = useChatAnywhereSessionsState();
  const currentSession = sessions.find((s) => s.id === currentSessionId);
  const chatName = currentSession?.name || "New Chat";
  const isMobile = useIsMobile();

  return (
    <span
      className={`${styles.chatName}${isMobile ? " qwenpaw-chat-header-title-mobile-hide" : ""}`}
    >
      {chatName}
    </span>
  );
};

export default ChatHeaderTitle;
