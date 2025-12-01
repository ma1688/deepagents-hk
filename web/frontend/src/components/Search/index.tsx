import { useState } from 'react';
import { Search as SearchIcon, Calendar, ExternalLink, Loader2 } from 'lucide-react';
import { searchApi } from '@/api/client';
import { useChatStore } from '@/stores';
import { SearchResult, AnnouncementItem } from '@/types';
import styles from './Search.module.css';

export function SearchPanel() {
  const [stockCode, setStockCode] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [titleFilter, setTitleFilter] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { setIsStreaming } = useChatStore();

  // Set default dates
  useState(() => {
    const today = new Date();
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
    
    setToDate(today.toISOString().split('T')[0].replace(/-/g, ''));
    setFromDate(thirtyDaysAgo.toISOString().split('T')[0].replace(/-/g, ''));
  });

  const handleSearch = async () => {
    if (!stockCode.trim()) {
      setError('请输入股票代码');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const searchResult = await searchApi.searchAnnouncements({
        stockCode: stockCode.padStart(5, '0'),
        fromDate: fromDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
          .toISOString().split('T')[0].replace(/-/g, ''),
        toDate: toDate || new Date().toISOString().split('T')[0].replace(/-/g, ''),
        title: titleFilter || undefined,
      });
      setResult(searchResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : '搜索失败');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    // Handle both YYYY-MM-DD and YYYYMMDD formats
    if (dateStr.includes('-')) {
      return dateStr;
    }
    return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
  };

  return (
    <div className={styles.searchPanel}>
      <div className={styles.header}>
        <SearchIcon size={20} />
        <h3>公告搜索</h3>
      </div>

      <div className={styles.form}>
        {/* Stock Code */}
        <div className={styles.field}>
          <label>股票代码</label>
          <input
            type="text"
            value={stockCode}
            onChange={(e) => setStockCode(e.target.value.replace(/\D/g, ''))}
            placeholder="如 00700"
            maxLength={5}
          />
        </div>

        {/* Date Range */}
        <div className={styles.dateRange}>
          <div className={styles.field}>
            <label>开始日期</label>
            <input
              type="date"
              value={fromDate ? `${fromDate.slice(0, 4)}-${fromDate.slice(4, 6)}-${fromDate.slice(6, 8)}` : ''}
              onChange={(e) => setFromDate(e.target.value.replace(/-/g, ''))}
            />
          </div>
          <div className={styles.field}>
            <label>结束日期</label>
            <input
              type="date"
              value={toDate ? `${toDate.slice(0, 4)}-${toDate.slice(4, 6)}-${toDate.slice(6, 8)}` : ''}
              onChange={(e) => setToDate(e.target.value.replace(/-/g, ''))}
            />
          </div>
        </div>

        {/* Title Filter */}
        <div className={styles.field}>
          <label>标题关键词（可选）</label>
          <input
            type="text"
            value={titleFilter}
            onChange={(e) => setTitleFilter(e.target.value)}
            placeholder="如 配售、供股"
          />
        </div>

        {/* Search Button */}
        <button
          className={styles.searchBtn}
          onClick={handleSearch}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              搜索中...
            </>
          ) : (
            <>
              <SearchIcon size={16} />
              搜索公告
            </>
          )}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className={styles.error}>
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className={styles.results}>
          <div className={styles.resultHeader}>
            <span>找到 {result.totalCount} 条公告</span>
            {result.cached && (
              <span className={styles.cachedBadge}>已缓存</span>
            )}
          </div>

          <div className={styles.resultList}>
            {result.announcements.map((item, idx) => (
              <AnnouncementCard key={idx} item={item} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface AnnouncementCardProps {
  item: AnnouncementItem;
}

function AnnouncementCard({ item }: AnnouncementCardProps) {
  return (
    <a
      href={item.url || '#'}
      target="_blank"
      rel="noopener noreferrer"
      className={styles.announcementCard}
    >
      <div className={styles.cardContent}>
        <h4 className={styles.cardTitle}>{item.title}</h4>
        <div className={styles.cardMeta}>
          <span className={styles.cardDate}>
            <Calendar size={12} />
            {item.date}
          </span>
          {item.category && (
            <span className={styles.cardCategory}>{item.category}</span>
          )}
        </div>
      </div>
      {item.url && (
        <ExternalLink size={14} className={styles.cardLink} />
      )}
    </a>
  );
}

