import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Loader2, Bot, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { useChatStore, useUserStore, useConfigStore } from '@/stores';
import { createChatWebSocket } from '@/api/client';
import { WSMessage, Message } from '@/types';
import styles from './Chat.module.css';

export function Chat() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  const { userId } = useUserStore();
  const { config } = useConfigStore();
  const {
    messages,
    isStreaming,
    streamingContent,
    currentConversationId,
    ws,
    setWebSocket,
    setIsStreaming,
    appendStreamingContent,
    clearStreamingContent,
    addMessage,
    setCurrentConversation,
  } = useChatStore();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Initialize WebSocket
  useEffect(() => {
    if (!userId) return;
    
    const websocket = createChatWebSocket(userId);
    
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
          // Add assistant message to list
          if (data.messageId && streamingContent) {
            const assistantMessage: Message = {
              id: data.messageId,
              conversationId: data.conversationId || '',
              role: 'assistant',
              content: streamingContent,
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
    };
    
    setWebSocket(websocket);
    
    return () => {
      websocket.close();
    };
  }, [userId]);

  // Auto-resize textarea
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, []);

  useEffect(() => {
    adjustTextareaHeight();
  }, [input, adjustTextareaHeight]);

  const handleSend = useCallback(() => {
    if (!input.trim() || isStreaming || !ws) return;
    
    // Add user message
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      conversationId: currentConversationId || '',
      role: 'user',
      content: input.trim(),
      createdAt: new Date().toISOString(),
    };
    addMessage(userMessage);
    
    // Send to WebSocket
    ws.send(JSON.stringify({
      message: input.trim(),
      conversation_id: currentConversationId,
    }));
    
    setInput('');
    setIsStreaming(true);
  }, [input, isStreaming, ws, currentConversationId, addMessage, setIsStreaming]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasApiKey = config?.hasApiKey;

  return (
    <main className={styles.chatContainer}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <Bot className={styles.logo} size={28} />
          <div>
            <h1 className={styles.title}>HKEX Agent</h1>
            <p className={styles.subtitle}>港股智能分析助手</p>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className={styles.messagesContainer}>
        <div className={styles.messagesWrapper}>
          {messages.length === 0 && !streamingContent && (
            <div className={styles.emptyState}>
              <Bot size={48} className={styles.emptyIcon} />
              <h2>开始对话</h2>
              <p>向我询问任何关于港股公告的问题</p>
              <div className={styles.suggestions}>
                <button onClick={() => setInput('查询00700腾讯最近30天的公告')}>
                  查询腾讯最近公告
                </button>
                <button onClick={() => setInput('分析最新的配售公告')}>
                  分析配售公告
                </button>
                <button onClick={() => setInput('总结00875百济神州的财务报告')}>
                  总结财务报告
                </button>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`${styles.message} ${
                message.role === 'user' ? styles.userMessage : styles.assistantMessage
              }`}
            >
              <div className={styles.messageAvatar}>
                {message.role === 'user' ? (
                  <User size={20} />
                ) : (
                  <Bot size={20} />
                )}
              </div>
              <div className={styles.messageContent}>
                {message.role === 'user' ? (
                  <p>{message.content}</p>
                ) : (
                  <ReactMarkdown
                    components={{
                      code({ className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        const isInline = !match;
                        return isInline ? (
                          <code className={styles.inlineCode} {...props}>
                            {children}
                          </code>
                        ) : (
                          <SyntaxHighlighter
                            style={oneDark}
                            language={match[1]}
                            PreTag="div"
                            className={styles.codeBlock}
                          >
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        );
                      },
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                )}
              </div>
            </div>
          ))}

          {/* Streaming message */}
          {streamingContent && (
            <div className={`${styles.message} ${styles.assistantMessage}`}>
              <div className={styles.messageAvatar}>
                <Bot size={20} />
              </div>
              <div className={styles.messageContent}>
                <ReactMarkdown>{streamingContent}</ReactMarkdown>
                <span className={styles.cursor}>▋</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className={styles.inputContainer}>
        <div className={styles.inputWrapper}>
          {!hasApiKey && (
            <div className={styles.apiKeyWarning}>
              ⚠️ 请先在设置中配置API密钥
            </div>
          )}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={hasApiKey ? "输入消息，按Enter发送..." : "请先配置API密钥"}
            disabled={isStreaming || !hasApiKey}
            className={styles.textarea}
            rows={1}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming || !hasApiKey}
            className={styles.sendButton}
          >
            {isStreaming ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <Send size={20} />
            )}
          </button>
        </div>
        <p className={styles.inputHint}>
          Shift + Enter 换行，Enter 发送
        </p>
      </div>
    </main>
  );
}

