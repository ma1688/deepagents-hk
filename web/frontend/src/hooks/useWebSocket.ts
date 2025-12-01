import { useEffect, useCallback, useRef } from 'react';
import { useChatStore, useUserStore } from '@/stores';
import { WSMessage, Message } from '@/types';

export function useWebSocket() {
  const { userId } = useUserStore();
  const {
    ws,
    setWebSocket,
    setIsStreaming,
    appendStreamingContent,
    clearStreamingContent,
    addMessage,
    setCurrentConversation,
    streamingContent,
  } = useChatStore();
  
  const streamingContentRef = useRef(streamingContent);
  
  useEffect(() => {
    streamingContentRef.current = streamingContent;
  }, [streamingContent]);

  const connect = useCallback(() => {
    if (!userId || ws?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const websocket = new WebSocket(`${protocol}//${host}/ws/chat/ws/${userId}`);

    websocket.onopen = () => {
      console.log('WebSocket connected');
    };

    websocket.onmessage = (event) => {
      const data: WSMessage = JSON.parse(event.data);

      switch (data.type) {
        case 'info':
          if (data.conversationId) {
            setCurrentConversation(data.conversationId);
          }
          break;
        case 'content':
          appendStreamingContent(data.content || '');
          break;
        case 'done':
          if (data.messageId && streamingContentRef.current) {
            const assistantMessage: Message = {
              id: data.messageId,
              conversationId: data.conversationId || '',
              role: 'assistant',
              content: streamingContentRef.current,
              createdAt: new Date().toISOString(),
            };
            addMessage(assistantMessage);
          }
          clearStreamingContent();
          setIsStreaming(false);
          break;
        case 'error':
          console.error('Chat error:', data.content);
          clearStreamingContent();
          setIsStreaming(false);
          break;
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsStreaming(false);
    };

    websocket.onclose = () => {
      console.log('WebSocket closed');
      // Attempt to reconnect after 3 seconds
      setTimeout(() => connect(), 3000);
    };

    setWebSocket(websocket);
  }, [userId, ws]);

  const disconnect = useCallback(() => {
    if (ws) {
      ws.close();
      setWebSocket(null);
    }
  }, [ws, setWebSocket]);

  const sendMessage = useCallback(
    (message: string, conversationId?: string) => {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.error('WebSocket not connected');
        return false;
      }

      ws.send(
        JSON.stringify({
          message,
          conversation_id: conversationId,
        })
      );
      return true;
    },
    [ws]
  );

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected: ws?.readyState === WebSocket.OPEN,
    connect,
    disconnect,
    sendMessage,
  };
}

