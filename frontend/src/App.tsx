import React, { useState, useEffect } from 'react';
import { Dashboard } from './components/Dashboard';
import { StudentJoinView } from './components/StudentJoinView';

export const App: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>(window.location.pathname);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  if (currentPath.startsWith('/join/')) {
    const joinCode = currentPath.split('/join/')[1]?.split('/')[0] || '';
    return <StudentJoinView joinCode={joinCode} />;
  }

  return <Dashboard />;
};

export default App;
