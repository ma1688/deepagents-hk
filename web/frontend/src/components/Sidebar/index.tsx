import { useState, useEffect } from 'react';
import {
  MessageSquare,
  Plus,
  Settings,
  Trash2,
  Edit2,
  Check,
  X,
  BarChart3,
  Search,
  ChevronLeft,
  Menu,
} from 'lucide-react';
import { useChatStore, useUserStore, useConfigStore } from '@/stores';
import { historyApi } from '@/api/client';
import { ConversationListItem, TokenUsageSummary } from '@/types';
import styles from './Sidebar.module.css';

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [activeTab, setActiveTab] = useState<'history' | 'stats' | 'search'>('history');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [tokenStats, setTokenStats] = useState<TokenUsageSummary | null>(null);

  const { userId } = useUserStore();
  const { toggleConfigPanel } = useConfigStore();
  const {
    conversations,
    setConversations,
    currentConversationId,
    setCurrentConversation,
    setMessages,
    removeConversation,
    updateConversationTitle,
    addConversation,
    reset,
  } = useChatStore();

  // Load conversations
  useEffect(() => {
    if (!userId) return;
    
    historyApi.getConversations(userId).then(setConversations).catch(console.error);
  }, [userId, setConversations]);

  // Load token stats
  useEffect(() => {
    if (!userId || activeTab !== 'stats') return;
    
    historyApi.getTokenStats(userId, 30).then(setTokenStats).catch(console.error);
  }, [userId, activeTab]);

  const handleNewChat = () => {
    reset();
    setCurrentConversation(null);
  };

  const handleSelectConversation = async (conv: ConversationListItem) => {
    if (!userId) return;
    
    try {
      const fullConv = await historyApi.getConversation(userId, conv.id);
      setCurrentConversation(conv.id);
      setMessages(fullConv.messages);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  };

  const handleDeleteConversation = async (id: string) => {
    if (!userId) return;
    
    try {
      await historyApi.deleteConversation(userId, id);
      removeConversation(id);
      if (currentConversationId === id) {
        reset();
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleStartEdit = (conv: ConversationListItem) => {
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const handleSaveEdit = async () => {
    if (!userId || !editingId || !editTitle.trim()) return;
    
    try {
      await historyApi.updateConversation(userId, editingId, editTitle.trim());
      updateConversationTitle(editingId, editTitle.trim());
      setEditingId(null);
    } catch (error) {
      console.error('Failed to update title:', error);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return '今天';
    if (days === 1) return '昨天';
    if (days < 7) return `${days}天前`;
    return date.toLocaleDateString('zh-CN');
  };

  return (
    <>
      {/* Mobile toggle */}
      <button
        className={styles.mobileToggle}
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <Menu size={20} />
      </button>

      <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}>
        {/* Header */}
        <div className={styles.header}>
          <button className={styles.newChatBtn} onClick={handleNewChat}>
            <Plus size={18} />
            <span>新对话</span>
          </button>
          <button
            className={styles.collapseBtn}
            onClick={() => setIsCollapsed(!isCollapsed)}
          >
            <ChevronLeft size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className={styles.tabs}>
          <button
            className={`${styles.tab} ${activeTab === 'history' ? styles.active : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <MessageSquare size={16} />
            <span>历史</span>
          </button>
          <button
            className={`${styles.tab} ${activeTab === 'stats' ? styles.active : ''}`}
            onClick={() => setActiveTab('stats')}
          >
            <BarChart3 size={16} />
            <span>统计</span>
          </button>
          <button
            className={`${styles.tab} ${activeTab === 'search' ? styles.active : ''}`}
            onClick={() => setActiveTab('search')}
          >
            <Search size={16} />
            <span>搜索</span>
          </button>
        </div>

        {/* Content */}
        <div className={styles.content}>
          {/* History Tab */}
          {activeTab === 'history' && (
            <div className={styles.conversationList}>
              {conversations.length === 0 ? (
                <div className={styles.emptyList}>
                  <MessageSquare size={24} />
                  <p>暂无对话记录</p>
                </div>
              ) : (
                conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`${styles.conversationItem} ${
                      currentConversationId === conv.id ? styles.active : ''
                    }`}
                  >
                    {editingId === conv.id ? (
                      <div className={styles.editMode}>
                        <input
                          type="text"
                          value={editTitle}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit()}
                          autoFocus
                        />
                        <button onClick={handleSaveEdit}>
                          <Check size={14} />
                        </button>
                        <button onClick={() => setEditingId(null)}>
                          <X size={14} />
                        </button>
                      </div>
                    ) : (
                      <>
                        <button
                          className={styles.convButton}
                          onClick={() => handleSelectConversation(conv)}
                        >
                          <MessageSquare size={16} />
                          <div className={styles.convInfo}>
                            <span className={styles.convTitle}>{conv.title}</span>
                            <span className={styles.convMeta}>
                              {conv.messageCount} 条消息 · {formatDate(conv.updatedAt)}
                            </span>
                          </div>
                        </button>
                        <div className={styles.convActions}>
                          <button onClick={() => handleStartEdit(conv)}>
                            <Edit2 size={14} />
                          </button>
                          <button onClick={() => handleDeleteConversation(conv.id)}>
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Stats Tab */}
          {activeTab === 'stats' && (
            <div className={styles.statsContainer}>
              {tokenStats ? (
                <>
                  <div className={styles.statCard}>
                    <h4>总Token使用</h4>
                    <div className={styles.statValue}>
                      {(tokenStats.totalInputTokens + tokenStats.totalOutputTokens).toLocaleString()}
                    </div>
                    <div className={styles.statDetail}>
                      输入: {tokenStats.totalInputTokens.toLocaleString()} | 
                      输出: {tokenStats.totalOutputTokens.toLocaleString()}
                    </div>
                  </div>
                  <div className={styles.statCard}>
                    <h4>总费用（30天）</h4>
                    <div className={styles.statValue}>
                      ¥{tokenStats.totalCostYuan.toFixed(4)}
                    </div>
                  </div>
                  <div className={styles.dailyStats}>
                    <h4>每日使用</h4>
                    {tokenStats.dailyStats.slice(0, 7).map((stat) => (
                      <div key={stat.id} className={styles.dailyStat}>
                        <span>{stat.date}</span>
                        <span>{stat.inputTokens + stat.outputTokens} tokens</span>
                        <span>¥{stat.costYuan}</span>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className={styles.emptyList}>
                  <BarChart3 size={24} />
                  <p>暂无统计数据</p>
                </div>
              )}
            </div>
          )}

          {/* Search Tab */}
          {activeTab === 'search' && (
            <SearchPanel />
          )}
        </div>

        {/* Footer */}
        <div className={styles.footer}>
          <button className={styles.settingsBtn} onClick={toggleConfigPanel}>
            <Settings size={18} />
            <span>设置</span>
          </button>
        </div>
      </aside>
    </>
  );
}

// Search Panel Component
function SearchPanel() {
  const [stockCode, setStockCode] = useState('');
  const [days, setDays] = useState(30);
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async () => {
    if (!stockCode.trim()) return;
    
    setIsLoading(true);
    try {
      const { searchApi } = await import('@/api/client');
      const result = await searchApi.getRecentAnnouncements(stockCode.padStart(5, '0'), days);
      setResults(result.announcements);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.searchPanel}>
      <div className={styles.searchInputs}>
        <input
          type="text"
          placeholder="股票代码（如00700）"
          value={stockCode}
          onChange={(e) => setStockCode(e.target.value)}
          maxLength={5}
        />
        <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={7}>7天</option>
          <option value={30}>30天</option>
          <option value={90}>90天</option>
        </select>
        <button
          className="btn-primary"
          onClick={handleSearch}
          disabled={isLoading || !stockCode.trim()}
        >
          {isLoading ? '搜索中...' : '搜索'}
        </button>
      </div>

      <div className={styles.searchResults}>
        {results.length === 0 ? (
          <div className={styles.emptyList}>
            <Search size={24} />
            <p>输入股票代码搜索公告</p>
          </div>
        ) : (
          results.map((item, idx) => (
            <a
              key={idx}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.resultItem}
            >
              <span className={styles.resultTitle}>{item.title}</span>
              <span className={styles.resultDate}>{item.date}</span>
            </a>
          ))
        )}
      </div>
    </div>
  );
}

