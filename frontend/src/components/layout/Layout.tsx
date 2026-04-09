import { Outlet } from 'react-router-dom';
import Header from './Header';
import Footer from './Footer';
import { BackgroundMusicPlayer } from '@/components/music/BackgroundMusicPlayer';
import { AchievementNotificationManager } from '@/components/dashboard/AchievementNotification';
import { RealTimeNotificationManager } from '@/components/dashboard/RealTimeFeedback';
import '@/styles/reading-mode.css';

const Layout = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />

      <BackgroundMusicPlayer />
      <AchievementNotificationManager />
      <RealTimeNotificationManager />
    </div>
  );
};

export default Layout;
