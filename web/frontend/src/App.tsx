import { useEffect } from 'react';
import { useUserStore } from '@/stores';
import { Layout } from '@/components/Layout';
import { Chat } from '@/components/Chat';
import { Sidebar } from '@/components/Sidebar';
import { ConfigPanel } from '@/components/Config';

function App() {
  const { initializeUser } = useUserStore();
  
  useEffect(() => {
    initializeUser();
  }, [initializeUser]);

  return (
    <Layout>
      <Sidebar />
      <Chat />
      <ConfigPanel />
    </Layout>
  );
}

export default App;

