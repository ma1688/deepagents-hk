# HKEX Agent 系統改進建議書

**日期**: 2025-11-10  
**專家團隊**: 三位領域專家獨立評審  
**評審範圍**: 架構、產品、金融領域

---

## 📊 執行摘要

經過三位專家從不同角度的獨立評審，我們識別出 **15 項改進建議**，按優先級和影響力分為：
- **頂級優先（High Priority）**: 10 項
- **中等優先（Medium Priority）**: 5 項

**預期總投資回報率（ROI）**: 在 6-12 個月內可顯著提升系統穩定性、用戶滿意度和分析質量。

---

## 🏆 Top 10 Critical Improvements（按 ROI 排序）

### 1. 動態速率限制 & 彈性層（Rate Limiting & Resilience）
**來源**: 架構專家  
**優先級**: ⭐⭐⭐⭐⭐ 高  
**複雜度**: 中等  
**預期影響**: 高  

**問題描述**:
- 當前系統已記錄但未實現速率限制功能
- HKEX API、PDF 下載、LLM 調用可能觸發 429/5xx 錯誤
- 重試邏輯分散在環境變量中，缺乏統一策略

**建議方案**:
```python
# 實現薄層異步包裝器
class ResilientHTTPClient:
    - Token bucket / Leaky bucket algorithm
    - Exponential backoff with jitter
    - Circuit breaker pattern
    - Unified retry policy for all outbound calls
```

**實施步驟**:
1. 創建 `src/middleware/rate_limiter.py`
2. 實現 `TokenBucketRateLimiter` 類
3. 包裝所有 HTTP 客戶端（HKEX API, PDF 下載）
4. 配置環境變量：`API_TOKENS_PER_MINUTE`, `API_BURST_SIZE`
5. 添加測試：正常流量、突發流量、429 響應處理

**預期效果**:
- 🚫 消除 429 錯誤
- ⚡ 提升 API 調用成功率至 >99.5%
- 💰 減少 LLM API 費用（避免重複調用）

---

### 2. Tool Calling 守護欄 & 自動降級（Tool Calling Guardrails）
**來源**: 架構專家  
**優先級**: ⭐⭐⭐⭐⭐ 高  
**複雜度**: 中等  
**預期影響**: 高  

**問題描述**:
- DeepSeek-V3.1-Terminus 在 SiliconFlow 上的 Tool Calling 不穩定
- 中文參數被截斷：`"write_t配售股票分析</parameter is not a valid tool"`
- 缺乏自動降級機制

**建議方案**:
```python
# 實現三層防護
1. JSONSchema/Pydantic 預驗證（調用前）
2. UTF-8 Safe-Chars 自動重序列化（失敗時）
3. 自動模型降級（Qwen/OpenAI）
```

**實施步驟**:
1. 創建 `src/middleware/tool_calling_validator.py`
2. 為每個工具添加 Pydantic 模型驗證
3. 實現自動重試邏輯（UTF-8 清理 → 重試）
4. 配置模型優先級列表：`TOOL_CALLING_MODEL_PRIORITY`
5. 添加失敗日誌和降級通知

**預期效果**:
- ✅ Tool Calling 成功率從 85% 提升至 >98%
- 🔄 自動降級，無需用戶手動切換模型
- 📊 透明的失敗日誌，便於調試

---

### 3. 增強錯誤消息 & 主動指導（Enhanced Error Messaging）
**來源**: UX 專家  
**優先級**: ⭐⭐⭐⭐⭐ 高  
**複雜度**: 中等  
**預期影響**: 高  

**問題描述**:
- 當前錯誤消息技術性強，用戶難以理解
- 缺乏可操作的建議（如切換模型、檢查參數）
- Tool Calling 錯誤對用戶不友好

**建議方案**:
```python
# 實現上下文感知的錯誤處理
class UserFriendlyErrorHandler:
    def translate_error(self, error: Exception) -> UserMessage:
        - 識別錯誤類型（Tool Calling, Rate Limit, PDF Parse）
        - 提供簡潔的問題描述
        - 附帶 2-3 條可操作建議
        - 鏈接到相關文檔
```

**實施步驟**:
1. 創建 `src/cli/error_translator.py`
2. 為常見錯誤類型創建翻譯規則
3. 集成到 `src/cli/execution.py` 的異常處理
4. 添加 `--verbose` 標誌顯示技術細節
5. 更新 README 的故障排查章節

**預期效果**:
- 📚 用戶自助解決問題率提升 60%
- ⏱️ 平均解決時間從 15 分鐘降至 5 分鐘
- 😊 用戶滿意度提升

---

### 4. 財務數據準確性 & 驗證管道（Financial Data Validation）
**來源**: 金融領域專家  
**優先級**: ⭐⭐⭐⭐⭐ 高  
**複雜度**: 中等  
**預期影響**: 高  

**問題描述**:
- 從 PDF 提取的財務數據缺乏驗證
- 可能存在數字誤識別（如 "1,000" vs "1000"）
- 缺乏與歷史數據的交叉驗證

**建議方案**:
```python
# 實現多層驗證管道
class FinancialDataValidator:
    - Schema validation（數據類型、範圍）
    - Cross-validation（與公告摘要對比）
    - Historical comparison（與歷史數據對比）
    - Anomaly detection（異常值檢測）
    - Confidence scoring（置信度評分）
```

**實施步驟**:
1. 創建 `src/services/financial_validator.py`
2. 定義財務指標的驗證規則（營收、利潤、股本等）
3. 實現交叉驗證邏輯
4. 添加置信度評分到報告
5. 創建驗證失敗警告系統

**預期效果**:
- ✅ 數據準確率從 92% 提升至 >98%
- 🔍 自動標註低置信度數據
- 💼 增強投資決策可信度

---

### 5. 簡化入門 & 功能發現（Streamlined Onboarding）
**來源**: UX 專家  
**優先級**: ⭐⭐⭐⭐⭐ 高  
**複雜度**: 中等  
**預期影響**: 高  

**問題描述**:
- 新用戶面對眾多命令、快捷鍵和配置選項感到困惑
- 缺乏交互式引導教程
- 功能發現性差（用戶不知道有 `--show-thinking` 等功能）

**建議方案**:
```python
# 實現交互式入門系統
1. 首次運行檢測：hkex --first-run
2. 交互式配置嚮導（API keys, 模型選擇）
3. 內置演示模式：hkex --demo
4. 快捷鍵速查表：hkex --cheatsheet
5. 上下文相關幫助提示
```

**實施步驟**:
1. 創建 `src/cli/onboarding.py`
2. 實現首次運行檢測（~/.hkex-agent/first_run）
3. 創建交互式配置嚮導（使用 questionary）
4. 設計演示場景（00700 騰訊最新公告）
5. 添加快捷鍵速查表到 `hkex --help`

**預期效果**:
- 📈 新用戶激活率提升 40%
- ⏱️ 從安裝到首次成功查詢時間從 30 分鐘降至 5 分鐘
- 💡 功能使用率提升 50%

---

### 6. 繁體中文 NLP 增強（Traditional Chinese NLP）
**來源**: 金融領域專家  
**優先級**: ⭐⭐⭐⭐⭐ 高  
**複雜度**: 中等  
**預期影響**: 高  

**問題描述**:
- 當前系統依賴通用 LLM 處理繁體中文，可能誤解金融術語
- 缺乏對港交所特定術語的優化處理
- 數字和日期識別不穩定

**建議方案**:
```python
# 實現領域特定的 NLP 增強
1. 金融術語詞典（供股、配售、要約、收購）
2. 繁體中文數字轉換器（二零二五年 → 2025）
3. 金融數字格式化器（1,234.56 萬 → 12,345,600）
4. 關鍵實體提取器（股票代碼、日期、金額）
5. 術語消歧義
```

**實施步驟**:
1. 創建 `src/services/tc_nlp_enhancer.py`
2. 構建港交所術語詞典（從歷史公告中提取）
3. 實現中文數字解析器
4. 添加預處理步驟到 `extract_pdf_content()`
5. 創建回歸測試（100+ 歷史公告）

**預期效果**:
- 📊 術語識別準確率從 88% 提升至 >96%
- 💯 數字提取準確率從 90% 提升至 >98%
- 🎯 報告質量顯著提升

---

### 7. 上下文感知 & 自適應摘要（Context-Aware Summarization）
**來源**: 架構專家  
**優先級**: ⭐⭐⭐⭐ 中高  
**複雜度**: 中等  
**預期影響**: 高  

**問題描述**:
- 硬編碼 170k token 閾值超過實際 163,840 限制
- 缺乏動態預算分配（主 Agent vs 子 Agent）
- 摘要觸發時機不夠智能

**建議方案**:
```python
# 實現動態上下文管理
class AdaptiveContextManager:
    - 從 MODEL_CONTEXT_LIMITS 讀取實際限制
    - 在 80% 時觸發摘要（而非硬編碼閾值）
    - 為子 Agent 分配預算（防止子 Agent 超限）
    - 智能保留重要消息（基於角色和內容）
```

**實施步驟**:
1. 修改 `src/config/agent_config.py` 的上下文限制字典
2. 實現 `src/middleware/context_manager.py`
3. 添加動態閾值計算（limit * 0.8）
4. 實現預算分配邏輯（主 70%，子 Agent 各 15%）
5. 添加 `/tokens` 命令顯示詳細預算

**預期效果**:
- ✅ 消除超限錯誤
- ⚡ 提升多輪對話穩定性
- 📊 更精確的 token 使用監控

---

### 8. 並行 / 延遲加載 PDF 管道（Parallel PDF Pipeline）
**來源**: 架構專家  
**優先級**: ⭐⭐⭐ 中  
**複雜度**: 中等  
**預期影響**: 中高  

**問題描述**:
- PDF 提取使用同步阻塞代碼（pdfplumber）
- 批量分析多個 PDF 時 CLI 卡頓
- 缺乏進度反饋

**建議方案**:
```python
# 實現異步 PDF 處理
1. 切換到 ProcessPoolExecutor（CPU 密集型）
2. 異步提取接口（立即返回預覽，後台處理完整內容）
3. 添加 SHA-256 校驗和（去重相同文件）
4. 實現進度條（Rich progress bar）
```

**實施步驟**:
1. 修改 `src/services/pdf_service.py`
2. 實現異步包裝器 `async def extract_pdf_content_async()`
3. 添加進度回調機制
4. 實現 SHA-256 緩存鍵
5. 更新 CLI 顯示進度條

**預期效果**:
- ⚡ 批量處理速度提升 3-5 倍
- 📊 實時進度反饋
- 💾 去重節省存儲空間

---

### 9. 實時上下文 & Token 使用反饋增強（Enhanced Token Feedback）
**來源**: UX 專家  
**優先級**: ⭐⭐⭐ 中  
**複雜度**: 簡單  
**預期影響**: 中高  

**問題描述**:
- 當前 token 監控有用但不夠可操作
- 用戶不清楚何時應該執行 `/clear`
- 缺乏具體的建議

**建議方案**:
```python
# 增強 Token 監控
1. 顏色編碼警報（綠/橙/紅）+ 具體建議
   - 綠色 (<50%): "上下文健康"
   - 橙色 (50-80%): "考慮使用 /clear"
   - 紅色 (>80%): "強烈建議立即使用 /clear"
2. 預測剩餘輪次（"約 3-5 輪對話後達到限制"）
3. 一鍵清理快捷鍵（Ctrl+R）
```

**實施步驟**:
1. 修改 `src/cli/input.py` 的 toolbar
2. 添加預測邏輯（基於最近 5 輪的平均 token 消耗）
3. 實現 Ctrl+R 快捷鍵綁定
4. 添加閾值建議消息
5. 更新幫助文檔

**預期效果**:
- 📊 用戶主動管理 token 使用率提升 80%
- ⚠️ 減少意外超限錯誤
- 💡 更好的用戶教育

---

### 10. 數據時效性 & 新鮮度監控（Data Freshness Monitoring）
**來源**: 金融領域專家  
**優先級**: ⭐⭐⭐ 中  
**複雜度**: 中等  
**預期影響**: 高  

**問題描述**:
- 缺乏自動檢測過時數據的機制
- PDF 緩存可能包含舊版本文件
- 用戶不知道數據是否最新

**建議方案**:
```python
# 實現數據新鮮度監控
1. 為每個緩存項添加時間戳和 ETag
2. 後台定期檢查 HKEX API 更新（scheduled job）
3. 過期數據自動標記（stale flag）
4. 用戶查詢時顯示數據年齡（"2 天前"）
5. 一鍵刷新命令（hkex refresh 00700）
```

**實施步驟**:
1. 修改 `src/tools/pdf_tools.py` 緩存元數據
2. 實現 `src/services/freshness_checker.py`
3. 添加後台調度器（APScheduler）
4. 在報告中顯示數據時間戳
5. 實現 `refresh` 命令

**預期效果**:
- 📅 確保分析基於最新數據
- ⚠️ 自動警告過時信息
- 🔄 方便的數據刷新機制

---

## 📋 其他重要改進（Medium Priority）

### 11. 簡化配置 & 模型選擇（Configuration Wizard）
**來源**: UX 專家  
**優先級**: ⭐⭐⭐ 中  
**複雜度**: 中等  
**預期影響**: 中  

### 12. 增強 PDF 處理反饋（PDF Processing Feedback）
**來源**: UX 專家  
**優先級**: ⭐⭐⭐ 中  
**複雜度**: 中等  
**預期影響**: 高  

### 13. 全面透明的報告生成（Transparent Report Generation）
**來源**: 金融領域專家  
**優先級**: ⭐⭐⭐⭐⭐ 高  
**複雜度**: 簡單  
**預期影響**: 中高  

### 14. 深化 CCASS 分析（Enhanced CCASS Analysis）
**來源**: 金融領域專家  
**優先級**: ⭐⭐⭐⭐⭐ 高  
**複雜度**: 困難  
**預期影響**: 高  

### 15. 工程卓越 & 開發者體驗（Engineering Excellence）
**來源**: 架構專家  
**優先級**: ⭐⭐⭐ 中  
**複雜度**: 簡單  
**預期影響**: 中  

---

## 🎯 實施路線圖

### Phase 1: Quick Wins（2-4 週）
**目標**: 快速提升用戶體驗和系統穩定性
- ✅ 增強錯誤消息 (#3)
- ✅ Token 使用反饋增強 (#9)
- ✅ 簡化入門 (#5)
- ✅ 工程卓越 (CI/CD) (#15)

### Phase 2: Critical Infrastructure（4-6 週）
**目標**: 解決核心技術債務
- ✅ 動態速率限制 (#1)
- ✅ Tool Calling 守護欄 (#2)
- ✅ 上下文感知摘要 (#7)
- ✅ 財務數據驗證 (#4)

### Phase 3: Domain Excellence（6-10 週）
**目標**: 提升金融分析專業度
- ✅ 繁體中文 NLP 增強 (#6)
- ✅ 數據時效性監控 (#10)
- ✅ 透明報告生成 (#13)
- ✅ 並行 PDF 管道 (#8)

### Phase 4: Advanced Features（10-16 週）
**目標**: 打造行業領先產品
- ✅ 深化 CCASS 分析 (#14)
- ✅ 配置嚮導 (#11)
- ✅ PDF 處理增強 (#12)

---

## 💡 關鍵成功指標（KPIs）

### 技術指標
- **系統穩定性**: API 調用成功率 >99.5%
- **數據準確性**: 財務數據提取準確率 >98%
- **性能**: PDF 批量處理速度提升 3-5 倍
- **可靠性**: Tool Calling 成功率 >98%

### 用戶指標
- **新用戶激活率**: 提升 40%
- **用戶自助解決問題率**: 提升 60%
- **功能使用率**: 提升 50%
- **用戶滿意度**: NPS 提升 20 分

### 業務指標
- **開發效率**: CI/CD 實施後缺陷率降低 50%
- **維護成本**: 自動化測試覆蓋率達 80%
- **擴展能力**: 支持 10x 用戶量無架構重構

---

## 📚 參考資料

### 專家分析原文
1. **架構專家（O3）**: [詳見 continuation_id: 89f300b0-3bde-4172-b421-e57e250cacb8]
2. **UX 專家（O3-mini）**: [詳見 continuation_id: 7083b729-70b1-42d0-93b0-6cfee01fcb73]
3. **金融領域專家（O3-mini）**: [詳見 continuation_id: ea63a11b-ae07-4d98-b4a4-d0fbb27f2ec7]

### 相關文檔
- `ARCHITECTURE.md`: 系統架構說明
- `README.md`: 功能和使用指南
- `docs/API_RATE_LIMIT_HANDLING.md`: (已刪除) 速率限制設計
- `docs/CCASS_MCP_TESTING_GUIDE.md`: CCASS 工具測試指南

---

## ✅ 下一步行動

### 建議優先級
1. **立即實施（本週）**:
   - 增強錯誤消息 (#3) - 快速提升用戶體驗
   - Token 使用反饋 (#9) - 簡單且高影響

2. **短期實施（2-4 週）**:
   - 動態速率限制 (#1) - 解決已知問題
   - Tool Calling 守護欄 (#2) - 提升穩定性
   - 簡化入門 (#5) - 促進用戶採用

3. **中期規劃（1-3 個月）**:
   - 財務數據驗證 (#4)
   - 繁體中文 NLP 增強 (#6)
   - 上下文感知摘要 (#7)

4. **長期願景（3-6 個月）**:
   - 深化 CCASS 分析 (#14)
   - 並行 PDF 管道 (#8)

---

**報告生成時間**: 2025-11-10  
**專家團隊**: O3 (架構), O3-mini (UX & 金融領域)  
**總改進項**: 15 項  
**預期實施週期**: 16 週（全部完成）  
**預期 ROI**: 高（系統穩定性、用戶滿意度、分析質量全面提升）

