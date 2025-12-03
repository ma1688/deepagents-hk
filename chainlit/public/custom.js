// 自定义脚本 - 在登录页面添加注册链接
(function() {
    console.log('[CustomJS] 加载自定义脚本');
    
    function addRegisterLink() {
        // 查找登录按钮
        const buttons = document.querySelectorAll('button');
        let loginButton = null;
        
        buttons.forEach(btn => {
            const text = btn.textContent.trim();
            if (text === '登录' || text === 'Sign In' || text === 'Login') {
                loginButton = btn;
            }
        });
        
        if (!loginButton) {
            console.log('[CustomJS] 未找到登录按钮');
            return false;
        }
        
        // 检查是否已经添加了注册链接
        if (document.getElementById('register-link-container')) {
            return true;
        }
        
        console.log('[CustomJS] 找到登录按钮，添加注册链接');
        
        // 创建注册链接容器
        const linkContainer = document.createElement('div');
        linkContainer.id = 'register-link-container';
        linkContainer.style.cssText = `
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(0,0,0,0.1);
            font-size: 14px;
        `;
        
        linkContainer.innerHTML = `
            <span style="color: #666;">没有账号？</span>
            <a href="/public/register.html" 
               style="color: #e11d48; text-decoration: none; font-weight: 500; margin-left: 4px;">
               立即注册
            </a>
        `;
        
        // 在登录按钮的父元素后面插入
        const form = loginButton.closest('form');
        if (form) {
            form.appendChild(linkContainer);
            console.log('[CustomJS] 注册链接已添加');
            return true;
        }
        
        return false;
    }
    
    // 使用 MutationObserver 监听 DOM 变化
    let attempts = 0;
    const maxAttempts = 50;
    
    function tryAddLink() {
        if (addRegisterLink()) {
            return;
        }
        
        attempts++;
        if (attempts < maxAttempts) {
            setTimeout(tryAddLink, 100);
        }
    }
    
    // 页面加载后尝试添加
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', tryAddLink);
    } else {
        tryAddLink();
    }
    
    // 使用 MutationObserver 作为后备
    const observer = new MutationObserver(function(mutations) {
        addRegisterLink();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();
