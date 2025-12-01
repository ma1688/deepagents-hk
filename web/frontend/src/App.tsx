import { useEffect } from 'react';
import { useAuthStore } from '@/stores';
import { Layout } from '@/components/Layout';
import { Chat } from '@/components/Chat';
import { Sidebar } from '@/components/Sidebar';
import { ConfigPanel } from '@/components/Config';
import { AuthPage } from '@/components/Auth';

function App() {
  const { isAuthenticated, user } = useAuthStore();

  // Show auth page if not authenticated
  if (!isAuthenticated) {
    return <AuthPage />;
  }

  return (
    <Layout>
      <Sidebar />
      <Chat />
      <ConfigPanel />
    </Layout>
  );
}

export default App;

