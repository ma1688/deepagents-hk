import { useState } from 'react';
import { Mail, Lock, User, LogIn, UserPlus, ArrowRight, Loader2 } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { authApi } from '@/api/auth';
import styles from './Auth.module.css';

type AuthMode = 'login' | 'register' | 'guest';

export function AuthPage() {
  const [mode, setMode] = useState<AuthMode>('login');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const { setAuth, setLoading, setError, isLoading, error, clearError } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    
    if (mode === 'register' && password !== confirmPassword) {
      setError('密码不匹配');
      return;
    }
    
    setLoading(true);
    
    try {
      let response;
      
      if (mode === 'login') {
        response = await authApi.login(email, password);
      } else if (mode === 'register') {
        response = await authApi.register(email, username, password);
      } else {
        response = await authApi.createGuest();
      }
      
      setAuth(response.access_token, {
        id: response.user_id,
        email: response.email,
        username: response.username,
        isGuest: response.is_guest,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '操作失败');
    } finally {
      setLoading(false);
    }
  };

  const handleGuestLogin = async () => {
    clearError();
    setLoading(true);
    
    try {
      const response = await authApi.createGuest();
      setAuth(response.access_token, {
        id: response.user_id,
        email: response.email,
        username: response.username,
        isGuest: response.is_guest,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : '游客登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.authContainer}>
      <div className={styles.authCard}>
        {/* Logo */}
        <div className={styles.logo}>
          <div className={styles.logoIcon}>HK</div>
          <h1>HKEX Agent</h1>
          <p>港股智能分析系统</p>
        </div>

        {/* Tabs */}
        <div className={styles.tabs}>
          <button
            className={`${styles.tab} ${mode === 'login' ? styles.active : ''}`}
            onClick={() => setMode('login')}
          >
            <LogIn size={16} />
            登录
          </button>
          <button
            className={`${styles.tab} ${mode === 'register' ? styles.active : ''}`}
            onClick={() => setMode('register')}
          >
            <UserPlus size={16} />
            注册
          </button>
        </div>

        {/* Form */}
        <form className={styles.form} onSubmit={handleSubmit}>
          {/* Email */}
          <div className={styles.field}>
            <div className={styles.inputWrapper}>
              <Mail size={18} className={styles.inputIcon} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={mode === 'login' ? '邮箱或用户名' : '邮箱'}
                required={mode !== 'guest'}
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Username (register only) */}
          {mode === 'register' && (
            <div className={styles.field}>
              <div className={styles.inputWrapper}>
                <User size={18} className={styles.inputIcon} />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="用户名"
                  required
                  minLength={3}
                  maxLength={50}
                  disabled={isLoading}
                />
              </div>
            </div>
          )}

          {/* Password */}
          <div className={styles.field}>
            <div className={styles.inputWrapper}>
              <Lock size={18} className={styles.inputIcon} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="密码"
                required
                minLength={6}
                disabled={isLoading}
              />
            </div>
          </div>

          {/* Confirm Password (register only) */}
          {mode === 'register' && (
            <div className={styles.field}>
              <div className={styles.inputWrapper}>
                <Lock size={18} className={styles.inputIcon} />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="确认密码"
                  required
                  minLength={6}
                  disabled={isLoading}
                />
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className={styles.error}>
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            className={styles.submitBtn}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <>
                {mode === 'login' ? '登录' : '注册'}
                <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Divider */}
        <div className={styles.divider}>
          <span>或</span>
        </div>

        {/* Guest Login */}
        <button
          className={styles.guestBtn}
          onClick={handleGuestLogin}
          disabled={isLoading}
        >
          {isLoading ? (
            <Loader2 size={18} className="animate-spin" />
          ) : (
            <>
              <User size={18} />
              游客模式（无需注册）
            </>
          )}
        </button>

        {/* Footer */}
        <p className={styles.footer}>
          游客数据将保存在本地，注册后可同步至云端
        </p>
      </div>
    </div>
  );
}

